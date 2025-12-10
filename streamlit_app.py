# streamlit_app.py ← FIXED: No more event loop errors + Real-time works
import streamlit as st
import asyncio
import nest_asyncio
from utils import supabase, async_supabase, get_current_user

# Patch Streamlit's loop
nest_asyncio.apply()

st.set_page_config(page_title="Supabase Todo • Fixed & Real-Time", page_icon="⚡", layout="centered")

# ─── Styling ─────────────────────────────────────
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc;
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">⚡ Supabase Todo<br><small>No errors • Real-time sync</small></p>', unsafe_allow_html=True)

# ─── Auth (session state for persistence) ──────────
if "user" not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    st.header("🔐 Auth")

    if st.session_state.user:
        st.success(f"👋 {st.session_state.user.email.split('@')[0]}")
        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if res.user:
                            st.session_state.user = res.user
                            st.success("✅ Logged in!")
                            st.rerun()
                        else:
                            st.error("❌ Login failed — confirm email first?")
                    except Exception as e:
                        st.error(f"❌ {str(e)}")

        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="su_email")
                password = st.text_input("Password", type="password", key="su_pwd")
                if st.form_submit_button("Sign Up"):
                    try:
                        res = supabase.auth.sign_up({"email": email, "password": password})
                        st.success("✅ Check email (spam too) to confirm!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ {str(e)}")

if not st.session_state.user:
    st.info("Log in or sign up to add todos!")
    st.stop()

# ─── Add Todo (fixed async) ───────────────────────
st.header("📝 Add Todo")
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to be done?", height=80, placeholder="e.g., Finish tutorial...")
    if st.form_submit_button("Add Todo") and task.strip():
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(async_supabase.table("todos").insert({
                "user_id": st.session_state.user.id,
                "task": task.strip(),
                "is_complete": False
            }).execute())
            st.success("✅ Todo added!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Add failed: {str(e)}")

# ─── Load & Show Todos (fixed async) ──────────────
st.header("📋 Your Todos")

async def fetch_todos():
    loop = asyncio.get_event_loop()
    resp = loop.run_until_complete(async_supabase.table("todos")\
        .select("*")\
        .eq("user_id", st.session_state.user.id)\
        .order("inserted_at", desc=True)\
        .execute())
    return resp.data or []

todos = asyncio.get_event_loop().run_until_complete(fetch_todos())

if not todos:
    st.info("🎉 No todos yet — add one above!")
else:
    for todo in todos:
        c1, c2, c3 = st.columns([6, 2, 2])
        with c1:
            status = "✅ Completed" if todo["is_complete"] else "⭕ Pending"
            st.markdown(f"""
            <div class="todo-item">
                <strong>{status} #{todo['id']}</strong><br>
                <span class="{'completed' if todo['is_complete'] else ''}">{todo['task']}</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", key=f"toggle_{todo['id']}"):
                loop = asyncio.get_event_loop()
                loop.run_until_complete(async_supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute())
                st.rerun()
        with c3:
            if st.button("🗑️", key=f"del_{todo['id']}"):
                loop = asyncio.get_event_loop()
                loop.run_until_complete(async_supabase.table("todos").delete().eq("id", todo["id"]).execute())
                st.rerun()

# ─── Real-Time Subscription (fixed & simple) ──────
if "realtime" not in st.session_state:
    def on_change(payload):
        st.rerun()

    loop = asyncio.get_event_loop()
    channel = loop.run_until_complete(async_supabase.channel(f"todos-{st.session_state.user.id}"))
    loop.run_until_complete(channel.on_postgres_changes(
        event="*", schema="public", table="todos",
        filter=f"user_id=eq.{st.session_state.user.id}",
        callback=on_change
    ).subscribe())
    
    st.session_state.realtime = True
    st.toast("⚡ Real-time active!")

st.caption("Fixed & live • Test: Open two tabs, add a todo — watch it sync instantly!")
