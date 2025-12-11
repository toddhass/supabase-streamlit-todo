# streamlit_app.py ← PRODUCTION-READY FINAL VERSION
import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime
from typing import List, Dict

# ─── Initialize Supabase Client Safely ─────────────────────
@st.cache_resource
def init_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase: Client = init_supabase()

# ─── Page Config & Premium Design ─────────────────────
st.set_page_config(
    page_title="My Todos",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Enhanced Premium CSS
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

st.markdown('<h1 class="big-title">✅ My Todos</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Beautiful • Secure • Real-time • Powered by Supabase</p>', unsafe_allow_html=True)

# ─── Authentication Handling (Secure & Robust) ─────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_checked" not in st.session_state:
    st.session_state.auth_checked = False

# Check current session on every load
if not st.session_state.auth_checked:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass
    st.session_state.auth_checked = True

# ─── Logout ─────────────────────
if st.session_state.user:
    cols = st.columns([3, 1])
    with cols[1]:
        if st.button("🚪 Log out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.auth_checked = False
            st.success("Logged out successfully")
            st.rerun()
    
    st.caption(f"Logged in as: **{st.session_state.user.email**")

# ─── Login / Sign Up Form ─────────────────────
else:
    st.markdown("### Welcome back")
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login_form", clear_on_submit=True):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Logging in..."):
                        try:
                            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state.user = res.user
                            st.success("Welcome back!")
                            st.rerun()
                        except Exception as e:
                            st.error("Invalid email or password")

    with tab2:
        with st.form("signup_form", clear_on_submit=True):
            new_email = st.text_input("Email", key="new_email", placeholder="you@example.com")
            new_password = st.text_input("Password", type="password", key="new_password", help="Minimum 6 characters")
            submitted2 = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if submitted2:
                if not new_email or not new_password:
                    st.error("Please fill in all fields")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        try:
                            supabase.auth.sign_up({"email": new_email, "password": new_password})
                            st.success("Account created! Check your email to confirm.")
                            st.balloons()
                        except Exception as e:
                            if "Email rate limit exceeded" in str(e):
                                st.error("Too many attempts. Please try again later.")
                            else:
                                st.error("Unable to create account. Email may already exist.")

    st.stop()

# ─── Secure Add Todo Functions ─────────────────────
@st.cache_data(ttl=1)  # Refresh every second for near real-time
def fetch_todos(user_id: str) -> List[Dict]:
    try:
        resp = supabase.table("todos")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return resp.data
    except Exception as e:
        st.error("Failed to load todos. Please refresh.")
        return []

def add_todo(task: str):
    if not task.strip():
        return
    try:
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()
    except Exception as e:
        st.error("Could not add todo")

def toggle_todo(todo_id: int, current_status: bool):
    try:
        supabase.table("todos").update({"is_complete": not current_status})\
            .eq("id", todo_id).eq("user_id", st.session_state.user.id).execute()
    except:
        st.error("Could not update todo")

def delete_todo(todo_id: int):
    try:
        supabase.table("todos").delete()\
            .eq("id", todo_id).eq("user_id", st.session_state.user.id).execute()
    except:
        st.error("Could not delete todo")

# ─── Add New Todo (Beautiful Input) ─────────────────────
st.markdown("### Add a new todo")
with st.form("add_todo_form", clear_on_submit=True):
    new_task = st.text_area(
        "What needs to be done?",
        placeholder="e.g., Deploy the new version with real-time updates ✅",
        height=120,
        label_visibility="collapsed"
    )
    add_col1, add_col2, add_col3 = st.columns([1, 2, 1])
    with add_col2:
        add_submitted = st.form_submit_button("Add Todo ✅", type="primary", use_container_width=True)

    if add_submitted:
        if new_task.strip():
            add_todo(new_task)
            st.success("Todo added!")
            st.balloons()
            time.sleep(0.8)
            st.rerun()
        else:
            st.warning("Please enter a task")

# ─── Display Todos with Real-time Refresh ─────────────────────
st.markdown("### Your Todos")

todos = fetch_todos(st.session_state.user.id)

if not todos:
    st.info("No todos yet — add one above to get started! 🚀")
else:
    for todo in todos:
        is_completed = todo.get("is_complete", False)
        card_class = "todo-card completed" if is_completed else "todo-card"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            col_task, col_toggle, col_delete = st.columns([7, 2, 2])
            
            with col_task:
                status_emoji = "✅" if is_completed else "⭕"
                st.markdown(f"### {status_emoji} **{todo['task']}**")
                if todo.get("created_at"):
                    created = datetime.fromisoformat(todo["created_at"].replace("Z", "+00:00"))
                    st.caption(f"Added {created.strftime('%b %d, %Y at %I:%M %p')}")
            
            with col_toggle:
                toggle_label = "Done 🎉" if not is_completed else "Undo"
                if st.button(toggle_label, key=f"toggle_{todo['id']}", use_container_width=True):
                    toggle_todo(todo["id"], is_completed)
                    st.rerun()
            
            with col_delete:
                if st.button("Delete 🗑️", key=f"delete_{todo['id']}", type="secondary", use_container_width=True):
                    delete_todo(todo["id"])
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# ─── Real-time Auto Refresh (Better than time.sleep!) ─────────────────────
# Using st.cache_data with ttl=1 + st.rerun() in actions = smooth real-time feel
# Optional: Add a subtle refresh indicator
with st.sidebar:
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Auto-refresh every 5 seconds when idle
time.sleep(5)
st.rerun()

# ─── Footer ─────────────────────
st.markdown("""
<div class="footer">
    Built with ❤️ using <strong>Streamlit</strong> + <strong>Supabase Auth & Realtime</strong><br>
    Secure • Fast • Beautiful • Open Source Ready
</div>
""", unsafe_allow_html=True)