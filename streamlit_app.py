# streamlit_app.py ← FINAL WORKING REALTIME VERSION
import streamlit as st
from supabase import create_client
import threading

# --- Supabase Client (compatible with current supabase-py) ---
@st.cache_resource
def get_supabase():
    # The current supabase-py library does NOT accept an `options` dict with `realtime`
    # Instead, we create the client normally and enable realtime logging separately if needed
    client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return client

supabase = get_supabase()

# --- Load Todos ---
def load_todos(user_id):
    params = {"target_user_id": str(user_id), "status_filter": "All Tasks"}
    try:
        resp = supabase.rpc("get_user_todos", params).execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Load error: {e}")
        return []

# --- Handlers (no st.rerun() — realtime will trigger refresh) ---
def add_todo(task):
    if task.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()

def toggle_complete(todo_id, current):
    supabase.table("todos").update({"is_complete": not current}).eq("id", todo_id).execute()

def delete_todo(todo_id):
    supabase.table("todos").delete().eq("id", todo_id).execute()

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- Realtime listener (runs in background) ---
def start_realtime_listener(user_id):
    def listener():
        channel = supabase.channel("todos-changes")
        channel.on(
            "postgres_changes",
            {"event": "*", "schema": "public", "table": "todos", "filter": f"user_id=eq.{user_id}"},
            lambda p: st.session_state.__setitem__("refresh", True)
        ).subscribe(blocking=True)

    if "realtime_thread" not in st.session_state:
        t = threading.Thread(target=listener, daemon=True)
        t.start()
        st.session_state.realtime_thread = t
        st.session_state.refresh = False

# --- Page config ---
st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")
st.title("My Todos")

# --- Auth ---
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
    # Start realtime listener
    start_realtime_listener(user.id)

    st.button("Log out", on_click=logout)

    # Add new todo
    with st.form("add_form", clear_on_submit=True):
        new_task = st.text_input("What needs to be done?")
        add_btn = st.form_submit_button("Add")
        if add_btn and new_task:
            add_todo(new_task)

    # Load and display todos
    todos = load_todos(user.id)

    if not todos:
        st.info("No todos yet — add one above!")
    else:
        data = []
        for t in todos:
            data.append({
                "Task": t["task"],
                "Done": st.checkbox("", value=t["is_complete"], key=f"done_{t['id']}", on_change=toggle_complete, args=(t["id"], t["is_complete"])),
                "Delete": st.button("Delete", key=f"del_{t['id']}", on_click=delete_todo, args=(t["id"],))
            })
        st.table(data)

    # Realtime trigger
    if st.session_state.get("refresh", False):
        st.session_state.refresh = False
        st.rerun()

else:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                try:
                    resp = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    st.session_state.user = resp.user
                    st.success("Logged in!")
                    st.rerun()
                except:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("signup"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                if len(pw) < 6:
                    st.error("Password too short")
                else:
                    try:
                        supabase.auth.sign_up({"email": email, "password": pw})
                        st.success("Check your email to confirm")
                    except:
                        st.error("Sign up failed")

    st.stop()