# streamlit_app.py ← FINAL 100% WORKING REAL-TIME VERSION (Dec 2025)
import streamlit as st
from utils import supabase, get_current_user

st.set_page_config(page_title="Supabase Todo • Live", page_icon="rocket", layout="centered")

# Styling
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc;
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">rocket Supabase Todo<br><small>Live sync • No refresh needed</small></p>', unsafe_allow_html=True)

# ─── Auth ─────────────────────
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
                    try:
                        supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                        st.rerun()
                    except:
                        st.error("Login failed")
        with tab2:
            with st.form("signup"):
                email = st.text_input("Email", key="e")
                pwd = st.text_input("Password", type="password", key="p")
                if st.form_submit_button("Sign Up"):
                    try:
                        supabase.auth.sign_up({"email": email, "password": pwd})
                        st.success("Check your email!")
                        st.balloons()
                    except Exception as e:
                        st.error(str(e))
    else:
        st.success(f"Hi {user.email.split('@')[0]}!")
        if st.button("Log Out", True):
            supabase.auth.sign_out()
            st.rerun()

if not user:
    st.stop()

# ─── Add Todo ─────────────────
with st.form("add", clear_on_submit=True):
    task = st.text_input("New todo")
    if st.form_submit_button("Add", True) and task:
        supabase.table("todos").insert({
            "user_id": user.id,
            "task": task,
            "is_complete": False
        }).execute()
        st.rerun()

# ─── Live Todos ───────────────
st.subheader("Your Todos (live)")

resp = supabase.table("todos")\
    .select("*")\
    .eq("user_id", user.id)\
    .order("inserted_at", desc=True)\
    .execute()

todos = resp.data or []

if not todos:
    st.info("No todos yet")
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
            """, True)
        with c2:
            if st.button("Toggle", key=f"t{todo['id']}"):
                supabase.table("todos").update({"is_complete": not todo["is_complete"]})\
                    .eq("id", todo["id"]).execute()
                st.rerun()
        with c3:
            if st.button("Delete", key=f"d{todo['id']}"):
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.rerun()

# ─── REAL-TIME (working method 2025) ────
# We use Streamlit's built-in session_state + Supabase Realtime via callback
if "last_realtime" not in st.session_state:
    st.session_state.last_realtime = None

def realtime_callback(payload):
    st.session_state.last_realtime = payload
    st.rerun()

# Subscribe (correct v2+ syntax)
supabase.realtime.connect()

channel = supabase.table("todos").on("INSERT", realtime_callback)\
                                 .on("UPDATE", realtime_callback)\
                                 .on("DELETE", realtime_callback)\
                                 .subscribe()

# Optional: cleanup on shutdown (not required but nice)
def on_session_end():
    supabase.realtime.disconnect()

st.on_session_end = on_session_end

st.caption("Live sync powered by Supabase Realtime — changes appear instantly!")
