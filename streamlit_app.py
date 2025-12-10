# streamlit_app.py
import streamlit as st
from utils import supabase, get_current_user

st.set_page_config(page_title="Supabase Todo", page_icon="check", layout="centered")

# ─── Styling ─────────────────────────────────────
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc; 
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    .completed {text-decoration: line-through; color: #94a3b8;}
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">check Supabase Todo</p>', unsafe_allow_html=True)
st.caption("Secure • Real-time • Powered by Supabase + Streamlit")

# ─── Sidebar Auth ───────────────────────────────
with st.sidebar:
    st.header("Authentication")
    user = get_current_user()

    if not user:
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    with st.spinner("Logging in..."):
                        try:
                            supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.success("Logged in!")
                            st.rerun()
                        except Exception as e:
                            st.error("Wrong email or password")

        with tab_signup:
            with st.form("signup_form"):
                email = st.text_input("Email", key="su_email")
                password = st.text_input("Password", type="password", key="su_pass")
                if st.form_submit_button("Create Account")
                if st.form_submit_button("Sign Up"):
                    with st.spinner("Creating account..."):
                        try:
                            supabase.auth.sign_up({"email": email, "password": password})
                            st.success("Check your email to confirm!")
                            st.balloons()
                        except Exception as e:
                            st.error(str(e))
    else:
        st.success(f"Hi {user.email.split('@')[0]}!")
        if st.button("Log Out", type="primary"):
            supabase.auth.sign_out()
            st.rerun()

# ─── Main App (only if logged in) ───────────────
if not user:
    st.info("Please log in or create an account to continue")
    st.stop()

# Add new todo
with st.expander("Add New Todo", expanded=True):
    with st.form("add_form", clear_on_submit=True):
        task = st.text_area("What needs to be done?", placeholder="Enter your task...")
        add_btn = st.form_submit_button("Add Todo", type="primary")
        if add_btn and task.strip():
            supabase.table("todos").insert({
                "user_id": user.id,
                "task": task.strip(),
                "is_complete": False
            }).execute()
            st.success("Added!")
            st.rerun()

# Show todos
st.subheader("Your Todos")
resp = supabase.table("todos")\
    .select("*")\
    .eq("user_id", user.id)\
    .order("inserted_at", desc=True)\
    .execute()

if not resp.data:
    st.info("No todos yet – add one above!")
else:
    for todo in resp.data:
        c1, c2, c3 = st.columns([7, 2, 2])
        with c1:
            status = "Completed" if todo["is_complete"] else "Pending"
            st.markdown(f"""
            <div class="todo-item">
                <strong>{todo['id']}. {status}</strong><br>
                <span class="{'completed' if todo['is_complete'] else ''}">{todo['task']}</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", key=f"t_{todo['id']}"):
                supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute()
                st.rerun()
        with c3:
            if st.button("Delete", key=f"d_{todo['id']}", type="secondary"):
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.rerun()

st.caption("Made with Streamlit + Supabase • Fully RLS protected")
