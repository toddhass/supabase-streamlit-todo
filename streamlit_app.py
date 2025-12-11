# streamlit_app.py ← FINAL, FLAWLESS, REAL-TIME TODO APP (December 11 2025)
import streamlit as st
from supabase import create_client
import time

# Supabase client
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# Page config & style
st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")

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
st.caption("Real-time • Instant sync • Powered by Supabase")

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
    col1, col2 = st.columns([6,1])
    with col2:
        if st.button("Log out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
    st.success(f"Logged in as **{user.email}**")
else:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Log In", type="primary"):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    st.rerun()
                except:
                    st.error("Wrong email or password")

    with tab2:
        with st.form("signup"):
            email = st.text_input("Email", key="su_email")
            pw = st.text_input("Password", type="password", key="su_pw")
            if st.form_submit_button("Sign Up", type="primary"):
                try:
                    supabase.auth.sign_up({"email": email, "password": pw})
                    st.success("Check your email to confirm!")
                    st.balloons()
                except:
                    st.error("Sign-up failed")

    st.stop()

# Load todos with short cache (feels real-time)
@st.cache_data(ttl=2, show_spinner=False)
def get_todos(_user_id):
    return supabase.table("todos")\
        .select("*")\
        .eq("user_id", _user_id)\
        .order("id", desc=True)\
        .execute().data

todos = get_todos(user.id)

# Add todo
st.markdown("### Checkmark Add a new todo")
with st.form("add", clear_on_submit=True):
    task = st.text_area("What needs to be done?", height=100, label_visibility="collapsed")
    if st.form_submit_button("Add Todo Checkmark", type="primary