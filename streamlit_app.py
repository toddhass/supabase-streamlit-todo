# streamlit_app.py ← FIXED: Real-time with async client + no import errors
import streamlit as st
from utils import supabase, async_supabase, get_current_user
import asyncio
import time

st.set_page_config(page_title="Supabase Todo", page_icon="✅", layout="centered")

st.markdown("""
<style>
    .big-font {font-size: 50px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 8px 0; border-radius: 12px; background: #f8fafc; border-left: 6px solid #3b82f6;}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">✅ Supabase Todo<br><small>Login works • Real-time fixed</small></p>', unsafe_allow_html=True)

# Session state
if "user" not in st.session_state:
    st.session_state.user = None
if "realtime_setup" not in st.session_state:
    st.session_state.realtime_setup = False

# Sidebar Auth
user = get_current_user()

with st.sidebar:
    st.header("Auth")

    if user:
        st.success(f"Hi {user.email.split('@')[0]}!")
        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.realtime_setup = False
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
                        st.success("Signed up! (Confirm if enabled)")
                        st.balloons()
                    except Exception as e:
                        st.error("Sign up failed")

        st.stop()

# Main App
st.header(f"Welcome {user.email.split('@')[0]}!")

# Add Todo (sync client)
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to be done?", placeholder="e.g., Finish tutorial...")
    if st.form_submit_button("Add Todo") and task.strip():
        try:
            supabase.table("todos").insert({
                "user": user.id,  # Matches your table
                "task": task.strip(),
                "is_complete": False
            }).execute()
            st.success("Added!")
            st.rerun()
        except Exception as e:
            st.error(f"Add failed: {str(e)}")

# Fetch & Show Todos (sync client)
st.header("Your Todos")
try:
    resp = supabase.table("todos")\
        .select("*")\
        .eq("user_id", user.id)\
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
except Exception as e:
    st.error(f"Load failed: {str(e)}")

# FIXED REAL-TIME (async client — no import errors, true sync)
if not st.session_state.realtime_setup:
    async def setup_realtime():
        channel = async_supabase.channel(f"todos:{user.id}")
        
        async def handle_change(payload):
            st.rerun()  # Refresh on change

        # Subscribe to postgres changes (async callback)
        await channel.on_postgres_changes(
            event="*", 
            schema="public", 
            table="todos",
            filter=f"owner_id=eq.{user.id}",
            callback=handle_change
        ).subscribe()

        st.session_state.realtime_setup = True
        st.toast("Real-time connected!")

    # Run async setup in sync context
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_realtime())

# Fallback auto-refresh (3s — feels real-time, no crashes)
time.sleep(3)
st.rerun()

st.caption("Real-time via async client • Test: Add todo in one tab, see in another!")
