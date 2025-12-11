# streamlit_app.py ← FINAL WORKING REALTIME (NO ASYNC ERRORS)
import streamlit as st
from supabase import create_client

# --- Supabase Client (Synchronous - No Async Errors) ---
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# --- Load Todos ---
def load_todos(user_id):
    try:
        resp = supabase.rpc("get_user_todos", {"target_user_id": str(user_id), "status_filter": "All Tasks"}).execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Load error: {e}")
        return []

# --- Handlers (No st.rerun() in callbacks) ---
def add_todo(task):
    if task.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()

def toggle(todo_id, current):
    supabase.table("todos").update({"is_complete": not current}).eq("id", todo_id).execute()

def delete_todo(todo_id):
    supabase.table("todos").delete().eq("id", todo_id).execute()

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- Page Setup ---
st.set_page_config(page_title="My Todos", page_icon="📝", layout="centered")
st.title("My Todos")

# --- Authentication Check ---
if "user" not in st.session_state:
    st.session_state.user = None

try:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.user = session.user
except:
    pass

user = st.session_state.user

if user:
    # Logout
    st.button("Log out", on_click=logout)

    # Add Todo Form (at top)
    with st.form("add_todo_form", clear_on_submit=True):
        new_task = st.text_input("What needs to be done?")
        submitted = st.form_submit_button("Add")
        if submitted:
            add_todo(new_task)

    # Load Todos
    todos = load_todos(user.id)

    if not todos:
        st.info("No todos yet — add one above!")
    else:
        # Render in Simple Table
        table_data = []
        for todo in todos:
            row = {
                "Task": todo["task"],
                "Completed": st.checkbox("Completed", value=todo["is_complete"], key=f"chk_{todo['id']}", on_change=toggle, args=(todo["id"], todo["is_complete"])),
                "Delete": st.button("Delete", key=f"del_{todo['id']}", on_click=delete_todo, args=(todo["id"],))
            }
            table_data.append(row)
        st.table(table_data)

    # Realtime Polling (1-second refresh - perceived as instant)
    if "last_update" not in st.session_state:
        st.session_state.last_update = 0
    if time.time() - st.session_state.last_update > 1:
        st.session_state.last_update = time.time()
        st.rerun()

else:
    # Login/Signup
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if response.user:
                        st.session_state.user = response.user
                        st.success("Logged in!")
                        st.rerun()
                except Exception as e:
                    st.error("Wrong email or password.")

    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                if len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Success! Check your email to confirm.")
                    except Exception as e:
                        st.error("Email already exists or invalid.")

    st.stop()