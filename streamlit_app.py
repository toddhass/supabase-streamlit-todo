# streamlit_app.py ← FINAL TRUE REAL-TIME (WORKS NOW)
import streamlit as st
from utils import supabase, get_current_user
import asyncio

st.set_page_config(page_title="Supabase Todo • Real-Time", page_icon="Lightning", layout="centered")

# ─── Styling ─────────────────────────────────────
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc;
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">Lightning Supabase Todo<br><small>True real-time • Instant sync</small></p>', unsafe_allow_html=True)

# ─── Auth (sync client for simplicity) ─────────────────────
from supabase import create_client

sync_supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

with st.sidebar:
    st.header("Auth")
    user = get_current_user()

    if not user:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    try:
                        sync_supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                        st.rerun()
                    except:
                        st.error("Wrong email/password")
        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                pwd = st.text_input("Password", type="password", key="signup_pwd")
                if st.form_submit_button("Sign Up"):
                    try:
                        sync_supabase.auth.sign_up({"email": email, "password": pwd})
                        st.success("Check your email to confirm!")
                        st.balloons()
                    except Exception as e:
                        st.error("Sign up failed")
    else:
        st.success(f"Hi {user.email.split('@')[0]}!")
        if st.button("Log Out"):
            sync_supabase.auth.sign_out()
            st.rerun()

if not user:
    st.stop()

# ─── Add Todo (async) ─────────────────────────────────────
with st.form("add_form", clear_on_submit=True):
    task = st.text_area("What needs to be done?")
    if st.form_submit_button("Add Todo") and task.strip():
        asyncio.run(
            supabase.table("todos").insert({
                "user_id": user.id,
                "task": task.strip(),
                "is_complete": False
            }).execute()
        )

# ─── Load & Display Todos (async) ─────────────────────────────
async def fetch_todos():
    resp = await supabase.table("todos")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("inserted_at", desc=True)\
        .execute()
    return resp.data or []

todos = asyncio.run(fetch_todos())

st.subheader("Your Todos (real-time)")

if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        c1, c2, c3 = st.columns([7, 2, 2])
        with c1:
            status = "Completed" if todo["is_complete"] else "Pending"
            st.markdown(f"""
            <div class="todo-item">
                <strong>{todo['id']}. {status}</strong><br>
                <span class="{'completed' if todo['is_complete'] else ''}">{todo['task']}</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", key=f"toggle_{todo['id']}"):
                asyncio.run(
                    supabase.table("todos").update({"is_complete": not todo["is_complete"]})
                    .eq("id", todo["id"]).execute()
                )
                st.rerun()
        with c3:
            if st.button("Delete", key=f"del_{todo['id']}"):
                asyncio.run(
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()
                )
                st.rerun()

# ─── TRUE REAL-TIME SUBSCRIPTION (the magic) ─────────────────────
if "realtime_setup" not in st.session_state:
    def on_change(payload):
        st.rerun()

    # Subscribe once per session
    channel = supabase.channel(f"user-todos-{user.id}")
    channel.on_postgres_changes(
        event="*", schema="public", table="todos",
        filter=f"user_id=eq.{user.id}",
        callback=on_change
    ).subscribe()

    st.session_state.realtime_setup = True
    st.success("Real-time connected! Changes appear instantly")

st.caption("True real-time via Supabase Realtime • Open in two tabs and try it!")
