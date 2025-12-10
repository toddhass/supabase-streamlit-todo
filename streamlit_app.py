# streamlit_app.py ← LOGIN FIXED + REAL-TIME (Dec 2025)
import streamlit as st
from supabase import create_client
import asyncio

# ─── Initialize Supabase ─────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# Async client for DB ops
@st.cache_resource
def get_async_supabase():
    from supabase import acreate_client
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(acreate_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]))

async_supabase = get_async_supabase()

st.set_page_config(page_title="Supabase Todo • Live", page_icon="⚡", layout="centered")

# ─── Styling ─────────────────────────────────────
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc;
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">⚡ Supabase Todo<br><small>Login fixed • Real-time sync</small></p>', unsafe_allow_html=True)

# ─── Session State for User ─────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Auth Forms (in sidebar for space) ─────
with st.sidebar:
    st.header("🔐 Auth")

    # Logout (if logged in)
    if st.session_state.user and st.button("Log Out", type="secondary"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    # Check current session on load
    if not st.session_state.user:
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                st.session_state.user = session.user
                st.rerun()
        except:
            pass

    # Login form
    if not st.session_state.user:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            col1, col2 = st.columns(2)
            with col1:
                login_submitted = st.form_submit_button("Log In", use_container_width=True)
            if login_submitted:
                if not email or not password:
                    st.error("Enter email & password")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if res.user:
                            st.session_state.user = res.user
                            st.success("✅ Logged in!")
                            st.rerun()
                        else:
                            st.error("❌ Login failed — check email confirmation (spam folder?)")
                    except Exception as e:
                        st.error(f"❌ {str(e)} — Wrong email/password?")

        # Sign up form
        st.markdown("---")
        with st.form("signup_form", clear_on_submit=True):
            new_email = st.text_input("New Email", key="new_email", placeholder="new@email.com")
            new_password = st.text_input("New Password", type="password", key="new_pass")
            col1, col2 = st.columns(2)
            with col1:
                signup_submitted = st.form_submit_button("Sign Up", use_container_width=True)
            if signup_submitted:
                if not new_email or not new_password:
                    st.error("Enter email & password")
                else:
                    try:
                        res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                        if res.user:
                            st.success("✅ Signed up! Check your email (including spam) to confirm before logging in.")
                            st.balloons()
                        else:
                            st.error("❌ Sign up failed")
                    except Exception as e:
                        st.error(f"❌ {str(e)}")

    # Show user if logged in
    if st.session_state.user:
        st.success(f"👋 Hi, {st.session_state.user.email.split('@')[0]}!")

if not st.session_state.user:
    st.info("👆 Log in or sign up in the sidebar to get started!")
    st.stop()

# ─── Add Todo Form ─────
st.header("📝 Add Todo")
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to be done?", height=80, placeholder="e.g., Buy milk...")
    col1, col2 = st.columns([3, 1])
    with col1:
        submitted = st.form_submit_button("Add Todo", use_container_width=True)
    if submitted and task.strip():
        try:
            asyncio.run(async_supabase.table("todos").insert({
                "user_id": st.session_state.user.id,
                "task": task.strip(),
                "is_complete": False
            }).execute())
            st.success("✅ Todo added instantly!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Add failed: {str(e)}")

# ─── Todos List (real-time) ─────
st.header("📋 Your Todos")

async def fetch_todos():
    try:
        resp = await async_supabase.table("todos")\
            .select("*")\
            .eq("user_id", st.session_state.user.id)\
            .order("inserted_at", desc=True)\
            .execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Load failed: {str(e)}")
        return []

todos = asyncio.run(fetch_todos())

if not todos:
    st.info("🎉 No todos yet — add one above!")
else:
    for todo in todos:
        col1, col2, col3 = st.columns([6, 2, 2])
        with col1:
            status_icon = "✅" if todo["is_complete"] else "⭕"
            task_class = "completed" if todo["is_complete"] else ""
            st.markdown(f"""
            <div class="todo-item">
                <strong>{status_icon} #{todo['id']} ({todo['task'][:50]}...)</strong><br>
                <span class="{task_class}">{todo['task']}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("Toggle", key=f"toggle_{todo['id']}"):
                asyncio.run(async_supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute())
                st.rerun()
        with col3:
            if st.button("🗑️", key=f"delete_{todo['id']}"):
                asyncio.run(async_supabase.table("todos").delete().eq("id", todo["id"]).execute())
                st.rerun()

# ─── Real-Time Setup (one-time per session) ─────
if "realtime_connected" not in st.session_state:
    def on_change(payload):
        st.rerun()

    channel = async_supabase.channel(f"todos-{st.session_state.user.id}")
    channel.on_postgres_changes(
        event="*", 
        schema="public", 
        table="todos",
        filter=f"user_id=eq.{st.session_state.user.id}",
        callback=on_change
    ).subscribe()
    
    st.session_state.realtime_connected = True
    st.toast("⚡ Real-time sync active — changes appear instantly!")

# ─── Footer ─────
st.markdown("---")
st.caption("⚡ Built with Supabase (Auth + Realtime) + Streamlit • RLS protected • Test in multiple tabs!")
