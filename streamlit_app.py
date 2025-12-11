# streamlit_app.py ← REAL-TIME VERSION (December 2025)
import streamlit as st
from supabase import create_client
import time
from datetime import datetime

# ─── Supabase client ─────────────────────
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")

# ─── Styling ─────────────────────
st.markdown("""
<style>
    .big-title {font-size: 4.5rem !important; font-weight: 900; text-align: center;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .todo-card {background:white; padding:1.8rem; margin:1.2rem 0; border-radius:18px;
                box-shadow:0 12px 40px rgba(0,0,0,.12); border-left:7px solid #667eea;}
    .completed {opacity:0.65; text-decoration:line-through; background:#f8f9fa; border-left-color:#28a745;}
    .realtime-badge {background:#10b981; color:white; padding:0.2rem 0.6rem; border-radius:999px; font-size:0.8rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">Checkmark My Todos</h1>', unsafe_allow_html=True)
st.caption("Real-time • Instant sync • Powered by Supabase Realtime")

# ─── Session recovery ─────────────────────
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
    if st.button("Log out", type="secondary"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    st.success(f"Logged in as {user.email}")
else:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])
    # (same login/signup code you already have — omitted for brevity)
    # → just keep your working version here
    st.stop()

# ─── REAL-TIME TODOS (this is the magic) ─────────────────────
if "todos" not in st.session_state:
    st.session_state.todos = []

def load_initial_todos():
    data = supabase.table("todos")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("id", desc=True)\
        .execute().data
    st.session_state.todos = data

# Load once on first run
if not st.session_state.todos:
    load_initial_todos()

# ─── Supabase Realtime subscription ─────────────────────
@st.cache_resource
def get_realtime_channel():
    channel = supabase.realtime_channel("todos-channel")
    channel.on_postgres_changes(
        event="*", schema="public", table="todos",
        filter=f"user_id=eq.{user.id}"
    ).on("postgres_changes", lambda payload: on_todo_change(payload))
    channel.subscribe()
    return channel

def on_todo_change(payload):
    todos = st.session_state.todos
    op = payload["eventType"]
    new_record = payload["new"]
    old_record = payload.get("old", {})

    if op == "INSERT":
        if new_record not in todos:
            todos.insert(0, new_record)
    elif op == "UPDATE":
        for i, t in enumerate(todos):
            if t["id"] == new_record["id"]:
                todos[i] = new_record
                break
    elif op == "DELETE":
        todos = [t for t in todos if t["id"] != old_record["id"]]
        st.session_state.todos = todos

    # Trigger rerun so Streamlit redraws instantly
    st.rerun()

# Start listening (only once)
get_realtime_channel()

# ─── Add Todo ─────────────────────
st.markdown("### Checkmark Add a new todo")
with st.form("add", clear_on_submit=True):
    task = st.text_area("What needs to be done?", height=100, label_visibility="collapsed")
    if st.form_submit_button("Add Todo Checkmark", type="primary", use_container_width=True):
        if task.strip():
            supabase.table("todos").insert({
                "user_id": user.id,
                "task": task.strip(),
                "is_complete": False
            }).execute()
            st.success("Added instantly!")
            st.balloons()
        else:
            st.warning("Write something first")

# ─── Display Todos (real-time updated) ─────────────────────
st.markdown(f"### Checkmark Your Todos  <span class='realtime-badge'>LIVE</span>", unsafe_allow_html=True)

if not st.session_state.todos:
    st.info("No todos yet — add one above!")
else:
    for todo in st.session_state.todos:
        completed = todo.get("is_complete", False)
        with st.container():
            st.markdown(f'<div class="todo-card {"completed" if completed else ""}">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([6,2,2])
            with c1:
                st.markdown(f"### {'Checkmark' if completed else 'Circle'} **{todo['task']}**")
            with c2:
                if st.button("Toggle", key=f"t{todo['id']}"):
                    supabase.table("todos").update({"is_complete": not completed})\
                        .eq("id", todo["id"]).execute()
            with c3:
                if st.button("Delete", key=f"d{todo['id']}", type="secondary"):
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()
            st.markdown('</div>', unsafe_allow_html=True)

# No more time.sleep() — Realtime does everything!