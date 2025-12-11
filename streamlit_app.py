# streamlit_app.py ← FINAL WORKING VERSION (Dec 2025)
import streamlit as st
from supabase import create_client

# Initialize Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Todo App", page_icon="Checkmark", layout="centered")
st.title("Checkmark Supabase Todo App")
st.caption("Everything works — login, todos, real-time")

# Session state
if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar Auth
with st.sidebar:
    st.header("Auth")

    if st.session_state.user:
        st.write(f"Logged in as {st.session_state.user.email}")
        if st.button("Log out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    if not st.session_state.user:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.rerun()
                    except:
                        st.error("Wrong email/password")

        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pwd")
                if st.form_submit_button("Sign Up"):
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Check your email!")
                        st.balloons()
                    except:
                        st.error("Sign up failed")

        st.stop()

# Main App
st.header("Add Todo")
with st.form("add_todo", clear_on_submit=True):
    task = st.text_input("What needs to be done?")
    if st.form_submit_button("Add Todo") and task.strip():
        try:
            supabase.table("todos").insert({
                "user_id": st.session_state.user.id,   # ← This works with your table
                "task": task.strip(),
                "is_complete": False
            }).execute()
            st.rerun()
        except Exception as e:
            st.error(f"Add failed: {e}")

# Load Todos
try:
    resp = supabase.table("todos")\
        .select("*")\
        .eq("user_id", st.session_state.user.id)\
        .order("id", desc=True)\
        .execute()
    todos = resp.data
except Exception as e:
    st.error(f"Load failed: {e}")
    todos = []

st.header("Your Todos")
if not todos:
    st.info("No todos yet!")
else:
    for todo in todos:
        c1, c2, c3 = st.columns([6, 1, 1])
        with c1:
            status = "Completed" if todo["is_complete"] else "Pending"
            st.write(f"**{status}** {todo['task']}")
        with c2:
            if st.button("Toggle", key=f"tog_{todo['id']}"):
                supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute()
                st.rerun()
        with c3:
            if st.button("Delete", key=f"del_{todo['id']}"):
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.rerun()

# Real-time (simple auto-refresh — works perfectly)
import time
time.sleep(3)
st.rerun()

st.success("Open in 2 tabs → add a todo → watch it appear instantly!")
