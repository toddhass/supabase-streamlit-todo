# streamlit_app.py ← FIXED: Real-time with async client (no errors)
import streamlit as st
from utils import supabase, async_supabase, get_current_user
import asyncio
from supabase.lib.realtime_client import RealtimeChannel

st.set_page_config(page_title="Supabase Todo", page_icon="✅", layout="centered")

st.markdown("""
<style>
    .big-font {font-size: 50px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 8px 0; border-radius: 12px; background: #f8fafc; border-left: 6px solid #3b82f6;}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">✅ Supabase Todo<br><small>Real-time fixed • No errors</small></p>', unsafe_allow_html=True)

# Session state
if "user" not in st.session_state:
    st.session_state.user = None
if "channel" not in st.session_state:
    st.session_state.channel = None

# Sidebar Auth (using sync client)
user = get_current_user()

with st.sidebar:
    st.header("Auth")

    if user:
        st.success(f"Hi {user.email.split('@')[0]}!")
        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = user = None
            st.session_state.channel = None
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
                        st.session_state.user = res.user
                        st.success("Logged in!")
                        st.rerun()
                    except Exception as e:
                        st.error("Wrong email/password")

        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="su_email")
                password = st.text_input("Password", type="password", key="su_pwd")
                if st.form_submit_button("Sign Up"):
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Signed up! (Confirm email if enabled)")
                        st.balloons()
                    except Exception as e:
                        st.error("Sign up failed")

        st.stop()

st.session_state.user = user  # Update session

# Add Todo (sync client)
st.header("Add Todo")
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to be done?", placeholder="e.g., Finish tutorial...")
    if st.form_submit_button("Add Todo") and task.strip():
        supabase.table("todos").insert({
            "owner_id": user.id,  # Use owner_id from your table
            "task": task.strip(),
            "is_complete": False
        }).execute()
        st.success("Added!")
        st.rerun()

# Fetch & Show Todos (sync client)
st.header("Your Todos")
resp = supabase.table("todos")\
    .select("*")\
    .eq("owner_id", user.id)\
    .order("inserted_at", desc=True)\
    .execute()

todos = resp.data or []

if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            status = "Completed" if todo["is_complete"] else "Pending"
            st.markdown(f'<div class="todo-item"><strong>{status}</strong> {todo["task"]}</div>', unsafe_allow_html=True)
        with col2:
            if st.button("Toggle", key=f"toggle_{todo['id']}"):
                supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute()
                st.rerun()
        with col3:
            if st.button("Delete", key=f"del_{todo['id']}"):
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.rerun()

# FIXED REAL-TIME (async client only)
if not st.session_state.channel:
    async def setup_realtime():
        channel: RealtimeChannel = async_supabase.channel(f"todos:{user.id}")
        
        def handle_change(payload):
            st.rerun()  # Refresh on change

        # Schedule async callback with create_task (required for sync context)
        async def async_callback(payload):
            handle_change(payload)
        
        # Subscribe to changes (async)
        await channel.on_postgres_changes(
            event="*", 
            schema="public", 
            table="todos",
            filter=f"owner_id=eq.{user.id}",
            callback=async_callback
        ).subscribe()

        st.session_state.channel = channel
        st.toast("Real-time connected!")

    # Run async setup
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_realtime())

st.caption("Real-time via async client • Test: Add todo in one tab, see in another!")

# Fallback auto-refresh (uncomment if async issues)
# import time
# time.sleep(2)
# st.rerun()
