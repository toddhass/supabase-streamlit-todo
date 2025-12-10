# streamlit_app.py  ← REAL-TIME VERSION
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
                    supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                    st.rerun()
        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="new_mail")
                pwd = st.text_input("Password", type="password", key="new_pwd")
                if st.form_submit_button("Sign Up"):
                    supabase.auth.sign_up({"email": email, "password": pwd})
                    st.success("Check your email to confirm!")
                    st.balloons()
    else:
        st.success(f"Hey {user.email.split('@')[0]}!")
        if st.button("Log Out", type="primary"):
            supabase.auth.sign_out()
            st.rerun()

# ─── Must be logged in ──────────────────────────
if not user:
    st.info("Log in or sign up to use real-time todos")
    st.stop()

# ─── REAL-TIME MAGIC STARTS HERE ─────────────────
# Create a placeholder that will auto-update
todo_container = st.empty()

with todo_container.container():
    st.subheader("Your Todos (real-time)")

    # Initial fetch
    resp = supabase.table("todos")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("inserted_at", desc=True)\
        .execute()

    todos = resp.data

    # Add new todo form (outside container so it stays on top)
    with st.form("add_form", clear_on_submit=True):
        new_task = st.text_area("Add a new todo", placeholder="What needs doing?")
        if st.form_submit_button("Add", type="primary") and new_task.strip():
            supabase.table("todos").insert({
                "user_id": user.id,
                "task": new_task.strip(),
                "is_complete": False
            }).execute()

    # Display todos
    Display current list
    if not todos:
        st.info("No todos yet — add one!")
    else:
        for todo in todos:
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
            with c3:
                if st.button("Delete", key=f"d_{todo['id']}", type="secondary"):
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()

# ─── REAL-TIME SUBSCRIPTION (the magic line) ─────
def on_realtime(payload):
    st.rerun()   # This refreshes the whole page instantly when anything changes

supabase.table("todos")\
    .on("INSERT", on_realtime)\
    .on("UPDATE", on_realtime)\
    .on("DELETE", on_realtime)\
    .subscribe()

# ─── Footer ─────────────────────────────────────
st.caption("Real-time powered by Supabase Realtime • Changes appear instantly across tabs & devices!")
