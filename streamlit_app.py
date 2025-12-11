# streamlit_app.py ← TRUE REALTIME (OFFICIAL WAY)
import streamlit as st
from supabase import create_client, Client
import json

# --- Supabase with Realtime ---
@st.cache_resource
def get_supabase() -> Client:
    client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return client

supabase = get_supabase()

# --- Load Todos ---
def load_todos():
    user_id = st.session_state.user.id
    resp = supabase.rpc("get_user_todos", {"target_user_id": str(user_id), "status_filter": "All Tasks"}).execute()
    return resp.data or []

# --- Handlers ---
def add_todo(task):
    if task.strip():
        supabase.table("todos").insert({"user_id": st.session_state.user.id, "task": task.strip()}).execute()

def toggle(todo_id, current):
    supabase.table("todos").update({"is_complete": not current}).eq("id", todo_id).execute()

def delete(todo_id):
    supabase.table("todos").delete().eq("id", todo_id).execute()

# --- Page ---
st.set_page_config(page_title="Realtime Todos", layout="centered")
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
    st.button("Log out", on_click=lambda: (supabase.auth.sign_out(), st.session_state.update(user=None), st.rerun()))

    with st.form("add", clear_on_submit=True):
        task = st.text_input("New todo")
        if st.form_submit_button("Add") and task:
            add_todo(task)

    # --- TRUE REALTIME (no polling) ---
    if "first_run" not in st.session_state:
        st.session_state.first_run = True
        # Subscribe once
        def on_change(payload):
            st.session_state.realtime_trigger = True

        supabase.realtime.on("postgres_changes", {
            "event": "*", "schema": "public", "table": "todos",
            "filter": f"user_id=eq.{user.id}"
        }, on_change).subscribe()

    # Trigger rerun if change detected
    if st.session_state.get("realtime_trigger"):
        st.session_state.realtime_trigger = False
        st.rerun()

    # Render todos
    todos = load_todos()
    for t in todos:
        c1, c2, c3 = st.columns([1, 8, 1])
        with c1:
            st.checkbox("", value=t["is_complete"], key=f"chk_{t['id']}", on_change=toggle, args=(t["id"], t["is_complete"]))
        with c2:
            st.write(t["task"])
        with c3:
            st.button("Delete", key=f"del_{t['id']}", on_click=delete, args=(t["id"],))

else:
    # Login / Signup (unchanged)
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])
    # ... same as before ...

    st.stop()