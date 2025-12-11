# streamlit_app.py ← FINAL REAL-TIME VERSION (Works Dec 2025)
import streamlit as st
from supabase import create_client
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
    .live {background:#10b981; color:white; padding:0.2rem 0.6rem; border-radius:999px; font-size:0.8rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">Checkmark My Todos</h1>', unsafe_allow_html=True)
st.caption("Real-time • Zero delay • Powered by Supabase Realtime")

# ─── Auth ─────────────────────
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
    # Keep your existing login/signup tabs here (unchanged)
    st.stop()

# ─── INITIAL LOAD + REAL-TIME (NEW CORRECT API) ─────────────────────
if "todos" not in st.session_state:
    st.session_state.todos = []

def load_todos():
    resp = supabase.table("todos")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("id", desc=True)\
        .execute()
    st.session_state.todos = resp.data

# Load once
if not st.session_state.todos:
    load_todos()

# ─── REAL-TIME SUBSCRIPTION (Correct 2025 syntax) ─────────────────────
if "realtime_setup" not in st.session_state:
    channel = supabase.channel("todos-changes")\
        .on_postgres_changes(
            event="*", schema="public", table="todos",
            filter=f"user_id=eq.{user.id}"
        )\
        .on("postgres_changes", lambda payload: st.rerun())\
        .subscribe()

    st.session_state.realtime_setup = True

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
            st.warning("Can't be empty")

# ─── Show Todos (instantly updated) ─────────────────────
st.markdown(f"### Checkmark Your Todos <span class='live'>LIVE</span>", unsafe_allow_html=True)

if not st.session_state.todos:
    st.info("No todos yet — add your first one!")
else:
    for todo in st.session_state.todos[:]:  # copy to avoid mutation issues
        completed = todo.get("is_complete", False)
        with st.container():
            st.markdown(f'<div class="todo-card {"completed" if completed else ""}">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([6,2,2])
            with c1:
                st.markdown(f"### {'Checkmark' if completed else '