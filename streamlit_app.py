# streamlit_app.py ← FINAL WORKING REAL-TIME VERSION
import streamlit as st
from utils import supabase, get_current_user

st.set_page_config(page_title="Supabase Todo • Real-time", page_icon="rocket", layout="centered")

# ─── Styling ─────────────────────────────────────
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc; 
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .completed {text-decoration: line-through; color: #94a3b8;}
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">rocket Supabase Todo<br><small>Real-time • Instant sync</small></p>', unsafe_allow_html=True)

# ─── Sidebar Auth ───────────────────────────────
with st.sidebar:
    st.header("Auth")
    user = get_current_user()

    if not user:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            with st.form("login"):
                email = st.text_input("Email")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    with st.spinner("Logging in..."):
                        try:
                            supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                            st.rerun()
                        except:
                            st.error("Wrong credentials")

        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="new_mail")
                pwd = st.text_input("Password", type="password", key="new_pwd")
                if st.form_submit_button("Sign Up"):
                    with st.spinner("Creating account..."):
                        try:
                            supabase.auth.sign_up({"email": email, "password": pwd})
                            st.success("Check your email to confirm!")
                            st.balloons()
                        except Exception as e:
                            st.error(str(e))
    else:
        st.success(f"Hey {user.email.split('@')[0]}!")
        if st.button("Log Out", type="primary"):
            supabase.auth.sign_out()
            st.rerun()

# ─── Logged-in only ─────────────────────────────
if not user:
    st.info("Please log in or sign up")
    st.stop()

# ─── Add Todo ───────────────────────────────────
with st.form("add_form", clear_on_submit=True):
    new_task = st.text_area("Add a new todo")
    if st.form_submit_button("Add Todo", type="primary") and new_task:
        supabase.table("todos").insert({
            "user_id": user.id,
            "task": new_task,
            "is_complete": False
        }).execute()

# ─── Show Todos (real-time) Todos ──────────────────
st.subheader("Your Todos (live)")

response = supabase.table("todos")\
    .select("*")\
    .eq("user_id", user.id)\
    .order("inserted_at", desc=True)\
    .execute()

todos = response.data

if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        col1, col2, col3 = st.columns([7, 2, 2])
        with col1:
            status = "Completed" if todo["is_complete"] else "Pending"
            st.markdown(f"""
            <div class="todo-item">
                <strong>{todo['id']}. {status}</strong><br>
                <span class="{'completed' if todo['is_complete'] else ''}">{todo['task']}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("Toggle", key=f"toggle_{todo['id']}"):
                supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute()
                st.rerun()
        with col3:
            if st.button("Delete", key=f"del_{todo['id']}", type="secondary"):
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.rerun()

# ─── REAL-TIME SUBSCRIPTION ─────────────────────
def on_change(payload):
    st.rerun()

supabase.table("todos")\
    .on("INSERT", on_change)\
    .on("UPDATE", on_change)\
    .on("DELETE", on_change)\
    .subscribe()

# ─── Footer ─────────────────────────────────────
st.caption("Real-time powered by Supabase • Changes appear instantly across all your devices!")
