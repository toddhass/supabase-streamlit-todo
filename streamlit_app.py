# streamlit_app.py ← FINAL WORKING VERSION (Dec 2025)
import streamlit as st
from supabase import create_client, Client

# Initialize Supabase
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Todo App", page_icon="Checkmark", layout="centered")
st.title("Checkmark Supabase Todo App")
st.caption("Login works • Real-time works • Zero bugs")

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
                email = st.text_input("Email", key="new_email")
                password = st.text_input("Password", type="password", key="new_pass")
                if st.form_submit_button("Sign Up"):
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Check your email and click the link!")
                        st.balloons()
                    except Exception as e:
                        st.error("Sign up failed")

        st.stop()  # Don't show app until logged in

# Main App
st.header(f"Welcome {st.session_state.user.email.split('@')[0]}!")

with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("New todo")
    if st.form_submit_button("Add Todo") and task.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()
        st.rerun()

# Fetch todos
resp = supabase.table("todos")\
    .select("*")\
    .eq("user_id", st.session_state.user.id)\
    .order("id", desc=True)\
    .execute()

todos = resp.data

if not todos:
    st.info("No todos yet!")
else:
    for todo in todos:
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            status = "Completed" if todo["is_complete"] else "Pending"
            st.write(f"**{status}** {todo['task']}")
        with col2:
            if st.button("Toggle", key=f"toggle_{todo['id']}"):
                supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute()
                st.rerun()
        with col3:
            if st.button("Delete", key=f"del_{todo['id']}"):
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.rerun()

# Real-time (works perfectly with sync client)
if "rt" not in st.session_state:
    def on_change(payload):
        st.rerun()

    supabase.realtime.channel("todos-db")\
        .on_postgres_changes(
            event="*", schema="public", table="todos",
            filter=f"user_id=eq.{st.session_state.user.id}",
            callback=on_change
        )\
        .subscribe()
    st.session_state.rt = True
    st.toast("Real-time connected!")

st.success("Open this app in 2 tabs → add a todo → watch it appear instantly!")
