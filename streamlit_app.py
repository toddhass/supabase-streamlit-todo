# streamlit_app.py ← FINAL WORKING REALTIME (WORKS ON STREAMLIT CLOUD)
import streamlit as st
from supabase import create_client
import time

# --- Supabase Client ---
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# --- Load Todos ---
def load_todos(user_id):
    try:
        resp = supabase.rpc("get_user_todos", {
            "target_user_id": str(user_id),
            "status_filter": "All Tasks"
        }).execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# --- Handlers ---
def add_todo(task):
    if task.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()

def toggle(todo_id, current):
    supabase.table("todos").update({"is_complete": not current}).eq("id", todo_id).execute()

def delete(todo_id):
    supabase.table("todos").delete().eq("id", todo_id).execute()

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- Page ---
st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")
st.title("My Todos")

# Auth
if "user" not in st.session_state:
    st.session_state.user = None

try:
    sess = supabase.auth.get_session()
    if sess and sess.user:
        st.session_state.user = sess.user
except:
    pass

user = st.session_state.user

if user:
    st.button("Log out", on_click=logout)

    # Add Todo
    with st.form("add", clear_on_submit=True):
        task = st.text_input("What needs to be done?")
        if st.form_submit_button("Add") and task:
            add_todo(task)

    # REALTIME: Poll every 1 second (only reliable way on Streamlit Cloud)
    placeholder = st.empty()

    while True:
        todos = load_todos(user.id)

        with placeholder.container():
            if not todos:
                st.info("No todos yet — add one above!")
            else:
                for t in todos:
                    c1, c2, c3 = st.columns([1, 8, 1])
                    with c1:
                        st.checkbox("", value=t["is_complete"],
                                  key=f"chk_{t['id']}", on_change=toggle,
                                  args=(t["id"], t["is_complete"]))
                    with c2:
                        st.write(t["task"])
                    with c3:
                        st.button("Delete", key=f"del_{t['id']}",
                                on_click=delete, args=(t["id"],))

        time.sleep(1)  # 1-second realtime
        st.rerun()     # This is allowed in main script

else:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    st.rerun()
                except:
                    st.error("Login failed")

    with tab2:
        with st.form("signup"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                try:
                    supabase.auth.sign_up({"email": email, "password": pw})
                    st.success("Check your email")
                except:
                    st.error("Sign up failed")

    st.stop()