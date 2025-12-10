# streamlit_app.py ← TRUE REAL-TIME (Async + Subscriptions)
import streamlit as st
import asyncio
from utils import supabase, get_current_user
from supabase.lib.realtime_client import RealtimeChannel
from typing import Any

st.set_page_config(page_title="Supabase Todo • Real-Time", page_icon="⚡", layout="centered")

# Styling
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc;
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">⚡ Supabase Todo<br><small>True Real-Time Sync</small></p>', unsafe_allow_html=True)

# Global state for channel
if "channel" not in st.session_state:
    st.session_state.channel = None

# ─── Auth (sync for simplicity) ──────────────────
with st.sidebar:
    st.header("Auth")
    user = get_current_user()

    if not user:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                pwd = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log In")
                if submitted:
                    try:
                        sync_sb = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
                        sync_sb.auth.sign_in_with_password({"email": email, "password": pwd})
                        st.rerun()
                    except:
                        st.error("Login failed")
        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="e")
                pwd = st.text_input("Password", type="password", key="p")
                submitted = st.form_submit_button("Sign Up")
                if submitted:
                    try:
                        sync_sb = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
                        sync_sb.auth.sign_up({"email": email, "password": pwd})
                        st.success("Check your email!")
                        st.balloons()
                    except Exception as e:
                        st.error(str(e))
    else:
        st.success(f"Hi {user.email.split('@')[0]}!")
        if st.button("Log Out"):
            sync_sb = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
            sync_sb.auth.sign_out()
            if st.session_state.channel:
                asyncio.run(st.session_state.channel.unsubscribe())
            st.session_state.channel = None
            st.rerun()

if not user:
    st.stop()

# ─── Add Todo ─────────────────
with st.form("add", clear_on_submit=True):
    task = st.text_input("New todo", placeholder="What needs doing?")
    submitted = st.form_submit_button("Add Todo")
    if submitted and task.strip():
        asyncio.run(supabase.table("todos").insert({
            "user_id": user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute())
        st.success("Added instantly!")

# ─── Real-Time Todos ──────────
st.subheader("Your Todos (⚡ Real-Time)")

async def load_todos():
    resp = await supabase.table("todos")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("inserted_at", desc=True)\
        .execute()
    return resp.data or []

async def setup_realtime():
    if st.session_state.channel:
        return  # Already subscribed

    # Create channel for user-specific todos
    channel: RealtimeChannel = supabase.channel(f"todos:{user.id}")

    def handle_event(payload: Any):
        st.rerun()  # Trigger re-render on change

    # Subscribe to events (async callback via create_task)
    import asyncio
    channel.on("postgres_changes", {
        "event": "*",
        "schema": "public",
        "table": "todos",
        "filter": f"user_id=eq.{user.id}"
    }, handle_event)

    await channel.subscribe()
    st.session_state.channel = channel
    st.success("Real-time connected! Changes sync instantly.")

# Load initial todos & setup subscription
todos = asyncio.run(load_todos())
await setup_realtime()  # Wait for subscription

if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        c1, c2, c3 = st.columns([7, 2, 2])
        with c1:
            status = "✓ Completed" if todo["is_complete"] else "○ Pending"
            st.markdown(f"""
            <div class="todo-item">
                <strong>{todo['id']}. {status}</strong><br>
                <span class="{'completed' if todo['is_complete'] else ''}">{todo['task']}</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", key=f"t{todo['id']}"):
                asyncio.run(supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute())
                st.rerun()
        with c3:
            if st.button("Delete", key=f"d{todo['id']}"):
                asyncio.run(supabase.table("todos").delete().eq("id", todo["id"]).execute())
                st.rerun()

# Cleanup on session end
def cleanup():
    if st.session_state.channel:
        asyncio.run(st.session_state.channel.unsubscribe())

st._on_session_end = cleanup  # Streamlit hack for cleanup

st.caption("⚡ True real-time via Supabase Postgres Changes • Syncs across tabs/devices!")
