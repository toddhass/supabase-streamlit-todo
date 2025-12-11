# streamlit_app.py ← BEAUTIFUL FINAL VERSION
import streamlit as st
from supabase import create_client
import time

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ─── BEAUTIFUL DESIGN ─────────────────────
st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")

# Custom CSS — makes it look like a premium app
st.markdown("""
<style>
    .css-1d391kg {padding-top: 2rem; padding-bottom: 3rem;}
    .big-title {font-size: 4rem !important; font-weight: 800; text-align: center; 
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .todo-card {background: white; padding: 1.5rem; margin: 1rem 0; border-radius: 16px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-left: 6px solid #667eea;}
    .completed {opacity: 0.6; text-decoration: line-through; background: #f8f9fa;}
    .stButton>button {border-radius: 12px; height: 3em; width: 100%;}
    .footer {text-align: center; margin-top: 4rem; color: #888; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

# Title with gradient
st.markdown('<h1 class="big-title">Checkmark My Todos</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Beautiful • Real-time • Powered by Supabase</p>", unsafe_allow_html=True)

# Session state
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Login / Logout ─────────────────────
if st.session_state.user:
    cols = st.columns([4,1])
    with cols[1]:
        if st.button("Log out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
    st.markdown(f"**Logged in as:** {st.session_state.user.email}")
else:
    with st.form("login", clear_on_submit=True):
        st.text_input("Email", key="email")
        st.text_input("Password", key="password", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Log In", type="primary"):
                try:
                    res = supabase.auth.sign_in_with_password({
                        "email": st.session_state.email,
                        "password": st.session_state.password
                    })
                    st.session_state.user = res.user
                    st.rerun()
                except:
                    st.error("Wrong email/password")
        with col2:
            if st.form_submit_button("Sign Up"):
                try:
                    supabase.auth.sign_up({
                        "email": st.session_state.email,
                        "password": st.session_state.password
                    })
                    st.success("Check your email to confirm!")
                    st.balloons()
                except:
                    st.error("Sign up failed")
    st.stop()

# ─── Add Todo (gorgeous input) ─────────────────────
st.markdown("### Checkmark Add a new todo")
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to be done?", placeholder="e.g., Finish the tutorial Checkmark", height=100)
    submitted = st.form_submit_button("Add Todo Checkmark", type="primary", use_container_width=True)
    if submitted and task.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()
        st.success("Todo added!")
        st.balloons()
        st.rerun()

# ─── Load & Display Todos (beautiful cards) ─────────────────────
resp = supabase.table("todos")\
    .select("*")\
    .eq("user_id", st.session_state.user.id)\
    .order("id", desc=True)\
    .execute()

todos = resp.data or []

st.markdown("### Checkmark Your Todos")
if not todos:
    st.info("No todos yet — time to add one! Checkmark")
else:
    for todo in todos:
        with st.container():
            card_class = "todo-card completed" if todo["is_complete"] else "todo-card"
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([6, 2, 2])
            with col1:
                check = "Checkmark" if todo["is_complete"] else "Circle"
                st.markdown(f"**{check} {todo['task']}**")
            with col2:
                if st.button("Toggle", key=f"tog_{todo['id']}"):
                    supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                        .eq("id", todo["id"]).execute()
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"del_{todo['id']}", type="secondary"):
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# Real-time auto-refresh
time.sleep(3)
st.rerun()

# Footer
st.markdown('<div class="footer">Built with Checkmark Streamlit + Supabase • Real-time • Beautiful</div>', unsafe_allow_html=True)
