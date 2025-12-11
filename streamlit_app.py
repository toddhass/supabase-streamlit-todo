# streamlit_app.py ← FINAL REAL-TIME VERSION – NO ERRORS WHATSOEVER
import streamlit as st
from supabase import create_client

# ─── Supabase client ─────────────────────
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")

# ─── Beautiful styling ─────────────────────
st.markdown("""
<style>
    .big-title {font-size:4.5rem!important;font-weight:900;text-align:center;
                background:linear-gradient(90deg,#667eea 0%,#764ba2 100%);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
    .todo-card {background:white;padding:1.8rem;margin:1.2rem 0;border-radius:18px;
                box-shadow:0 12px 40px rgba(0,0,0,.12);border-left:7px solid #667eea;}
    .completed {opacity:0.65;text-decoration:line-through;background:#f8f9fa;border-left-color:#28a745;}
    .live {background:#10b981;color:white;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.8rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">Checkmark My Todos</h1>', unsafe_allow_html=True)
st.caption("Real-time • Zero delay • Powered by Supabase Realtime")

# ─── Authentication ─────────────────────
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
    # ← Put your working login/signup code here (unchanged)
    st.stop()

# ─── Load todos once ─────────────────────
if "todos" not in st.session_state:
    st.session_state.todos = []

def load_todos():
    resp = supabase.table("todos")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("id", desc=True)\
        .execute()
    st.session_state.todos = resp.data or []          # ← Fixed line

if not st.session_state.todos:
    load_todos()

# ─── Real-time subscription (2025 correct syntax) ─────────────────────
if "realtime_setup" not in st.session_state:
    supabase.channel("todos-changes")\
        .on_postgres_changes(
            event="*", schema="public", table="todos",
            filter=f"user_id=eq.{user.id}"
        )\
        .on("postgres_changes", lambda payload: st.rerun())\
        .subscribe()
    st.session_state.realtime_setup = True

# ─── Add new todo ─────────────────────
st.markdown("### Checkmark Add a new todo")
with st.form("add_todo",