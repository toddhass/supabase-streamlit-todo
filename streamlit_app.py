# streamlit_app.py ← FINAL PRODUCTION-READY VERSION (100% working)
import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime
from typing import List, Dict

# ─── Initialize Supabase Client (cached) ─────────────────────
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_supabase()

# ─── Page Config & Beautiful Design ─────────────────────
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

# ─── SAFE Authentication State Management (fixes NameError) ─────────────────────
# Ensure session state keys exist
for key in ["user", "auth_checked"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "user" else False

# Recover active session on cold start (very important for Streamlit Cloud)
if not st.session_state.user and not st.session_state.auth_checked:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except Exception:
        pass
    finally:
        st.session_state.auth_checked = True

# Current user (safe access)
user = st.session_state.user

# ─── Logged-in User UI ─────────────────────
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

# ─── Login / Sign Up UI ─────────────────────
else:
    st.markdown("### Welcome! Please log in or create an account")
    tab1, tab2 = st.tabs(["Log