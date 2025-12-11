# streamlit_app.py ← FINAL, PERFECTLY WORKING VERSION (December 2025)
import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime
from typing import List, Dict

# ─── Supabase Client (cached) ─────────────────────
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_supabase()

# ─── Page Config & Design ─────────────────────
st.set_page_config(
    page_title="My Todos",
    page_icon="Checkmark",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .big-title {
        font-size: 4.5rem !important;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 3rem;}
    .todo-card {
        background: white;
        padding: 1.8rem;
        margin: 1.2rem 0;
        border-radius: 18px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
        border-left: 7px solid #667eea;
        transition: all 0.3s ease;
    }
    .todo-card:hover {transform: translateY(-4px); box-shadow: 0 20px 50px rgba(0,0,0,0.15);}
    .completed {
        opacity: 0.65;
        text-decoration: line-through;
        background: #f8f9fa;
        border-left-color: #28a745;
    }
    .stButton>button {
        border-radius: 12px;
        height: 3.2em;
        font-weight: 600;
    }
    .footer {
        text-align: center;
        margin-top: 5rem;
        padding: 2rem;
        color: #999;
        font-size: 0.95rem;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">Checkmark My Todos</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Beautiful • Secure • Real-time • Powered by Supabase</p>', unsafe_allow_html=True)

# ─── Safe Session State Initialization ─────────────────────
for key in ["user", "auth_checked"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "user" else False

# Recover session on cold start
if not st.session_state.user and not st.session_state.auth_checked:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except Exception:
        pass
    finally:
        st.session_state.auth_checked = True

user = st.session_state.user

# ─── Logged-in UI ─────────────────────
if user:
    cols = st.columns([3, 1])
    with cols[1]:
        if st.button("Log out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.auth_checked = False
            st.success("Logged out successfully")
            st.rerun()

    st.caption(f"Logged in as: **{user.email}**")

# ─── Login / Sign-up UI (fixed string) ─────────────────────
else:
    st.markdown("### Welcome! Please log in or create an account")
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])   # ← THIS LINE WAS BROKEN BEFORE

    with tab1:
        with st.form("login_form", clear_on_submit=True):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Please fill both fields")
                else:
                    with st.spinner("Logging in..."):
                        try:
                            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state.user = res.user
                            st.success("Welcome back!")
                            st.rerun()
                        except Exception:
                            st.error("Invalid credentials")

    with tab2:
        with st.form("signup_form", clear_on_submit=True):
            new_email = st.text_input("Email", placeholder="you@example.com")
            new_password = st.text_input("Password", type="password", help="Minimum 6 characters")
            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if submitted:
                if not new_email or not new_password:
                    st.error("Please fill both fields")
                elif len(new_password) < 6:
                    st.error("Password too short")
                else:
                    with st.spinner("Creating account..."):
                        try:
                            supabase.auth.sign_up({"email": new_email, "password": new_password})
                            st.success("Account created! Check your email to confirm.")
                            st.balloons()
                        except Exception as e:
                            st.error("Sign-up failed (email may already exist)")

    st.stop()

# ─── Helper Functions ─────────────────────
@st.cache_data(ttl=3, show_spinner=False)
def fetch_todos(_user_id: str) -> List[Dict]:
    try:
        resp = supabase.table("todos").select("*").eq("user_id", _user_id).order("created_at", desc=True).execute()
        return resp.data or []
    except:
        return []

def add_todo(task: str) -> bool:
    if not task.strip():
        return False
    try:
        supabase.table("todos").insert({
            "user_id": user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()
        return True
    except:
        st.error