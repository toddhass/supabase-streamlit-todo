# streamlit_app.py ← ENHANCED VERSION WITH DETAILED ERROR HANDLING (Dec 11, 2025)
import streamlit as st
from supabase import create_client
import time
from datetime import datetime

# Use Streamlit connection for secure, cached Supabase access
@st.cache_resource
def init_supabase():
    return st.connection("supabase", type="supabase")

supabase = init_supabase()

# Page configuration
st.set_page_config(page_title="My Todos", page_icon="✅", layout="centered")

# Styling
st.markdown("""
<style>
    .big-title {font-size: 4.5rem !important; font-weight: 900; text-align: center;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .todo-card {background: white; padding: 1.8rem; margin: 1.2rem 0; border-radius: 18px;
                box-shadow: 0 12px 40px rgba(0,0,0,0.12); border-left: 7px solid #667eea;}
    .completed {opacity: 0.65; text-decoration: line-through; background: #f8f9fa; border-left-color: #28a745;}
    .stButton > button {border-radius: 12px; height: 3.2em; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">✅ My Todos</h1>', unsafe_allow_html=True)

# Session state
if "user" not in st.session_state:
    st.session_state.user = None

# Recover session
try:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.user = session.user
except Exception as e:
    st.session_state.user = None  # Graceful fallback

user = st.session_state.user

# Logged-in UI
if user:
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
    st.caption(f"Logged in as: **{user.email}**")

else:
    # Login/Sign-up tabs
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", type="primary")
            if submitted:
                if not (email and password):
                    st.warning("Please enter email and password.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.success("Logged in successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {str(e).split(':', 1)[-1] if ':' in str(e) else str(e)}")
                        st.info("Check credentials or try resetting password.")

    with tab2:
        with st.form("signup"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            submitted = st.form_submit_button("Sign Up", type="primary")
            if submitted:
                if not (email and password and len(password) >= 6):
                    st.warning("Email required; password must be at least 6 characters.")
                else:
                    try:
                        res = supabase.auth.sign_up({"email": email, "password": password})
                        if res.user:
                            st.success("Account created! Check your email for confirmation (or disable confirmations in Supabase settings for instant access).")
                            st.balloons()
                        else:
                            st.warning("Sign-up initiated—check email.")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "already exists" in error_msg:
                            st.error("Email already registered. Try logging in or use password recovery.")
                        elif "disabled" in error_msg:
                            st.error("Sign-ups are disabled in project settings. Enable in Supabase dashboard.")
                        elif "rate limit" in error_msg:
                            st.error("Rate limit exceeded. Wait 1 minute and retry.")
                        else:
                            st.error(f"Sign-up failed: {str(e).split(':', 1)[-1] if ':' in str(e) else str(e)}")
                        st.info("Common fixes: Enable email provider, check SMTP settings, or verify project limits.")

    st.stop()

# Todos functionality (unchanged from prior working version for brevity)
def load_todos():
    try:
        return supabase.table("todos").select("*").eq("user_id", user.id).order("id", desc=True).execute().data or []
    except:
        return []

todos = load_todos()

st.markdown("### Add a New Todo")
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to be done?", height=100, label_visibility="collapsed")
    if st.form_submit_button("Add Todo ✅", type="primary", use_container_width=True) and task.strip():
        supabase.table("todos").insert({"user_id": user.id, "task": task.strip(), "is_complete": False}).execute()
        st.success("Todo added!")
        st.rerun()

st.markdown("### Your Todos")
if not todos:
    st.info("No todos yet. Add one above.")
else:
    for todo in todos:
        completed = todo.get("is_complete", False)
        with st.container():
            st.markdown(f'<div class="todo-card {"completed" if completed else ""}">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([6, 2, 2])
            with col1:
                st.markdown(f"### {'✅' if completed else '⭕'} **{todo['task']}**")
            with col2:
                if st.button("Toggle", key=f"t_{todo['id']}"):
                    supabase.table("todos").update({"is_complete": not completed}).eq("id", todo["id"]).execute()
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"d_{todo['id']}", type="secondary"):
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# Auto-refresh
time.sleep(5)
st.rerun()

st.markdown('<div style="text-align: center; color: #888; margin-top: 3rem;">Powered by Supabase & Streamlit</div>', unsafe_allow_html=True)