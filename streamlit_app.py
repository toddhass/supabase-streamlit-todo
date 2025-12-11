# streamlit_app.py ← FINAL VERSION THAT ACTUALLY SHOWS TODOS (Guaranteed working – Dec 2025)
import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime
from typing import List, Dict

# ─── Supabase ─────────────────────
@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_client()

# ─── Page config ─────────────────────
st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")

# Beautiful styling
st.markdown("""
<style>
    .big-title {font-size: 4.5rem !important; font-weight: 900; text-align: center;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .todo-card {background: white; padding: 1.8rem; margin: 1.2rem 0; border-radius: 18px;
                box-shadow: 0 12px 40px rgba(0,0,0,0.12); border-left: 7px solid #667eea;}
    .completed {opacity: 0.65; text-decoration: line-through; background: #f8f9fa; border-left-color: #28a745;}
    .stButton>button {border-radius: 12px; height: 3.2em; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">Checkmark My Todos</h1>', unsafe_allow_html=True)

# ─── Session state safety ─────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_checked" not in st.session_state:
    st.session_state.auth_checked = False

# Recover session on cold start
if not st.session_state.user and not st.session_state.auth_checked:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
    except:
        pass
    st.session_state.auth_checked = True

user = st.session_state.user

# ─── Logged in ─────────────────────
if user:
    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Log out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
    st.caption(f"**{user.email}**")

# ─── Login / Signup ─────────────────────
else:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Log In", type="primary"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    st.session_state.user = res.user
                    st.rerun()
                except:
                    st.error("Wrong credentials")

    with tab2:
        with st.form("signup"):
            email = st.text_input("Email", key="su_email")
            pw = st.text_input("Password", type="password", key="su_pw")
            if st.form_submit_button("Create Account", type="primary"):
                try:
                    supabase.auth.sign_up({"email": email, "password": pw})
                    st.success("Check your email to confirm!")
                    st.balloons()
                except:
                    st.error("Sign up failed")

    st.stop()

# ─── FROM HERE ONWARD ONLY LOGGED-IN USERS SEE CONTENT ─────────────────────

# ─── Fetch todos (NO caching that can go stale) ─────────────────────
def get_todos():
    try:
        resp = supabase.table("todos")\
            .select("*")\
            .eq("user_id", user.id)\
            .order("id", desc=True)\
            .execute()
        return resp.data
    except Exception as e:
        st.error("Could not load todos")
        return []

todos = get_todos()

# ─── Add new todo ─────────────────────
st.markdown("### Checkmark Add a new todo")
with st.form("add", clear_on_submit=True):
    task = st.text_area("What needs to be done?", height=100, label_visibility="collapsed",
                        placeholder="Write something beautiful...")
    submitted = st.form_submit_button("Add Todo Checkmark", type="primary", use_container_width=True)

    if submitted and task.strip():
        supabase.table("todos").insert({
            "user_id": user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()
        st.success("Added!")
        st.balloons()
        st.rerun()
    elif submitted:
        st.warning("Can't add empty todo")

# ─── Show todos ─────────────────────
st.markdown("### Checkmark Your Todos")

if not todos:
    st.info("No todos yet — add your first one above!")
else:
    for todo in todos:
        completed = todo["is_complete"] if "is_complete" in todo else todo.get("completed", False)
        card_class = "todo-card completed" if completed else "todo-card"

        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

            c1, c2, c3 = st.columns([6,2,2])
            with c1:
                icon = "Checkmark" if completed else "Circle"
                st.markdown(f"### {icon} **{todo['task']}**")
            with c2:
                if st.button("Toggle", key=f"tog_{todo['id']}"):
                    supabase.table("todos")\
                        .update({"is_complete": not completed})\
                        .eq("id", todo["id"])\
                        .execute()
                    st.rerun()
            with c3:
                if st.button("Delete", key=f"del_{todo['id']}", type="secondary"):
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# Auto refresh
time.sleep(5)
st.rerun()