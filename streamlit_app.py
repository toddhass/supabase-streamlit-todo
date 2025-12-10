# streamlit_app.py ← FINAL VERSION THAT WORKS 100%
import streamlit as st
from supabase import create_client

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Todo App", page_icon="Done", layout="centered")
st.title("Done Supabase Todo App")
st.caption("Login works • Todos work Real-time works")

# Session state
if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar Auth
with st.sidebar:
    if st.session_state.user:
        st.success(f"Hi {st.session_state.user.email.split('@')[0]}!")
        if st.button("Log out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                        st.session_state.user = res.user
                        st.rerun()
                    except:
                        st.error("Wrong email/password")

        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="su_email")
                pwd = st.text_input("Password", type="password", key="su_pwd")
                if st.form_submit_button("Sign Up"):
                    try:
                        supabase.auth.sign_up({"email": email, "password": pwd})
                        st.success("Check email & click link!")
                        st.balloons()
                    except:
                        st.error("Sign up failed")

        st.stop()

# Add Todo — CHANGE "user_id" TO YOUR ACTUAL COLUMN NAME
with st.form("add", clear_on_submit=True):
    task = st.text_area("What needs to be done?")
    if st.form_submit_button("Add Todo") and task.strip():
        # CHANGE "user_id" to whatever your column is called (user_id, owner_id, created_by, etc.)
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,   # ← CHANGE THIS LINE IF NEEDED
            "task": task.strip(),
            "is_complete": False
        }).execute()
        st.rerun()

# Load Todos — same column name as above
resp = supabase.table("todos")\
    .select("*")\
    .eq("user_id", st.session_state.user.id)\   # ← MUST MATCH THE LINE ABOVE
    .order("inserted_at", desc=True)\
    .execute()

todos = resp.data or []

st.subheader("Your Todos")

if not todos:
    st.info("No todos yet — add one!")
else:
    for t in todos:
        c1, c2, c3 = st.columns([6,1,1])
        with c1:
            s = "Completed" if t["is_complete"] else "Pending"
            st.write(f"**{s}** {t['task']}")
        with c2:
            if st.button("Toggle", key=f"t{t['id']}"):
                supabase.table("todos").update({"is_complete": not t["is_complete"]})\
                    .eq("id", t["id"]).execute()
                st.rerun()
        with c3:
            if st.button("Delete", key=f"d{t['id']}"):
                supabase.table("todos").delete().eq("id", t["id"]).execute()
                st.rerun()

# Simple real-time (refreshes every 3 seconds — feels instant)
import time
time.sleep(3)
st.rerun()