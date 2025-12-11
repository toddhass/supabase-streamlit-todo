# streamlit_app.py ← SIMPLIFIED VERSION
import streamlit as st
from supabase import create_client

# --- Supabase Client ---
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# --- Load Todos (All Tasks) ---
def load_todos(_user_id):
    params = {
        "target_user_id": str(_user_id),
        "status_filter": "All Tasks"
    }
    try:
        response = supabase.rpc("get_user_todos", params=params).execute()
        data = response.data or []
        return data
    except Exception as e:
        st.error(f"Failed to load todos: {str(e)}")
        return []

# --- Handlers ---
def update_todo_status(todo_id, new_status):
    supabase.table("todos").update({"is_complete": new_status}).eq("id", todo_id).execute()
    st.rerun()

def handle_add_todo(task_to_add):
    if task_to_add.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task_to_add.strip(),
            "is_complete": False
        }).execute()
        st.rerun()

def delete_todo(todo_id):
    supabase.table("todos").delete().eq("id", todo_id).execute()
    st.rerun()

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

    # Add Todo Form
    with st.form("add_todo_form", clear_on_submit=True):
        new_task = st.text_input("New Todo")
        submitted = st.form_submit_button("Add")
        if submitted:
            handle_add_todo(new_task)

    # Load Todos
    todos = load_todos(user.id)

    if not todos:
        st.info("No todos yet — add one above!")
    else:
        # Render in Table Format
        st.table([
            {
                "Task": todo["task"],
                "Completed": st.checkbox("Completed", value=todo["is_complete"], key=f"chk_{todo['id']}", on_change=update_todo_status, args=(todo["id"], not todo["is_complete"])),
                "Delete": st.button("Delete", key=f"del_{todo['id']}", on_click=delete_todo, args=(todo["id"],))
            } for todo in todos
        ])

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
                except:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                if len(password) < 6:
                    st.error("Password too short")
                else:
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Check email to confirm")
                    except:
                        st.error("Signup failed")

    st.stop()