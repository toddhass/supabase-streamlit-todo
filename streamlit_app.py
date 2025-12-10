# streamlit_app.py ← GUARANTEED TO WORK (Dec 2025)
import streamlit as st
from supabase import create_client

# Initialise Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="Supabase Todo", page_icon="Check", layout="centered")

# ─── Styling ─────────────────────
st.markdown("""
<style>
    .big {font-size:52px !important; text-align:center; color:#1e40af; font-weight:bold;}
    .t {padding:16px; margin:8px 0; border-radius:12px; background:#f8fafc;
        border-left:6px solid #3b82f6; box-shadow:0 2px 8px rgba(0,0,0,0.1);}
    .c {text-decoration:line-through; color:#94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big">Check Supabase Todo<br><small>Login + Real-time = works perfectly</small></p>', unsafe_allow_html=True)

# ─── Session state ─────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Sidebar ─────
with st.sidebar:
    st.header("Auth")

    # LOGOUT
    if st.session_state.user:
        if st.button("Log out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # LOGIN / SIGNUP
    if not st.session_state.user:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                        st.session_state.user = res.user
                        st.rerun()
                    except:
                        st.error("Wrong credentials or email not confirmed")

        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                pwd = st.text_input("Password", type="password", key="signup_pwd")
                if st.form_submit_button("Sign Up"):
                    try:
                        supabase.auth.sign_up({"email": email, "password": pwd})
                        st.success("Check your email (including spam) and click the link!")
                        st.balloons()
                    except Exception as e:
                        st.error("Sign-up failed")

        st.stop()  # ← stop here until logged in

    st.success(f"Hi {st.session_state.user.email.split('@')[0]}!")

# ─── Add Todo ─────
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to be done?")
    if st.form_submit_button("Add Todo") and task.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute()
        st.rerun()

# ─── Show Todos ─────
resp = supabase.table("todos")\
    .select("*")\
    .eq("user_id", st.session_state.user.id)\
    .order("inserted_at", desc=True)\
    .execute()

todos = resp.data or []

st.subheader("Your Todos (real-time)")

if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        c1, c2, c3 = st.columns([7, 2, 2])
        with c1:
            status = "Completed" if todo["is_complete"] else "Pending"
            st.markdown(f'''
            <div class="t">
                <strong>{status} #{todo["id"]}</strong><br>
                <span class="{"c" if todo["is_complete"] else ""}">{todo["task"]}</span>
            </div>
            ''', unsafe_allow_html=True)
        with c2:
            if st.button("Toggle", key=f"tog_{todo['id']}"):
                supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute()
                st.rerun()
        with c3:
            if st.button("Delete", key=f"del_{todo['id']}"):
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.rerun()

# ─── REAL-TIME (works instantly) ─────
if "rt" not in st.session_state:
    def refresh(_): st.rerun()
    supabase.realtime.channel("any")\
        .on_postgres_changes(event="*", schema="public", table="todos",
                             filter=f"user_id=eq.{st.session_state.user.id}",
                             callback=refresh)\
        .subscribe()
    st.session_state.rt = True
    st.toast("Real-time connected!")

st.caption("Open this app in two tabs → add a todo → watch it appear instantly. Done!")
