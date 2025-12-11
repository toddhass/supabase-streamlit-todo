import streamlit as st
from supabase import create_client
import threading

# Initialize Supabase client
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# Function to load todos via RPC
def load_todos(user_id, status_filter):
    params = {
        "target_user_id": str(user_id),
        "status_filter": status_filter
    }
    try:
        response = supabase.rpc("get_user_todos", params=params).execute()
        data = response.data or []
        return data
    except Exception as e:
        st.error(f"Failed to load todos: {str(e)}")
        return []

# Handlers
def update_todo_status(todo_id, new_status):
    supabase.table("todos").update({"is_complete": new_status}).eq("id", todo_id).execute()
    # No rerun here; realtime will handle

def handle_add_todo(task_to_add, user_id):
    if task_to_add.strip():
        supabase.table("todos").insert({
            "user_id": user_id,
            "task": task_to_add.strip(),
            "is_complete": False
        }).execute()
    # No rerun; realtime will handle

def delete_todo(todo_id):
    supabase.table("todos").delete().eq("id", todo_id).execute()
    # No rerun; realtime will handle

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# Realtime subscription in background thread
def setup_realtime(user_id):
    def realtime_listener():
        channel = supabase.channel('todo-changes')
        channel.on(
            'postgres_changes',
            {'event': '*', 'schema': 'public', 'table': 'todos', 'filter': f'user_id=eq.{user_id}'},
            lambda payload: st.session_state.__setitem__('data_changed', True)
        ).subscribe(blocking=True)

    if 'realtime_thread' not in st.session_state:
        thread = threading.Thread(target=realtime_listener)
        thread.daemon = True  # Daemon thread to exit with app
        thread.start()
        st.session_state['realtime_thread'] = thread
        st.session_state['data_changed'] = False

# Page config
st.set_page_config(page_title="Realtime Todos", page_icon="📝", layout="centered")

# Authentication
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
    # Setup realtime for this user
    setup_realtime(user.id)

    # Logout button
    st.button("Log out", on_click=logout)

    # Add todo
    st.header("Add Todo")
    new_task = st.text_input("Task")
    if st.button("Add"):
        handle_add_todo(new_task, user.id)
        new_task = ""  # Clear input

    # Filter
    st.header("Todos")
    filter_options = ["Active Tasks", "Completed Tasks", "All Tasks"]
    status_filter = st.selectbox("Filter", filter_options, index=0)

    # Load todos
    todos = load_todos(user.id, status_filter)

    # Display todos
    for todo in todos:
        col1, col2, col3 = st.columns([1, 8, 1])
        with col1:
            st.checkbox("Complete", value=todo["is_complete"], on_change=update_todo_status, args=(todo["id"], not todo["is_complete"]), key=f"chk_{todo['id']}")
        with col2:
            st.write(todo["task"])
        with col3:
            if st.button("Delete", key=f"del_{todo['id']}"):
                delete_todo(todo["id"])

    # Check for data change and rerun
    if st.session_state.get('data_changed', False):
        st.session_state['data_changed'] = False
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
                    except Exception as e:
                        st.error("Signup failed")

    st.stop()