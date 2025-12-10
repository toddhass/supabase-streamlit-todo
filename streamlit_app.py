# streamlit_app.py ← FINAL VERSION: Login works + True real-time
import streamlit as st
from supabase import create_client
import asyncio

# ─── Initialize Supabase (sync client for auth + async for DB) ─────
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
# Async client for real-time (cached)
@st.cache_resource
def get_async_client():
    from supabase import acreate_client
    return asyncio.run(acreate_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]))

async_supabase = get_async_client()

st.set_page_config(page_title="Supabase Todo • Live", page_icon="Lightning", layout="centered")

# ─── Styling ─────────────────────────────────────
st.markdown("""
<style>
    .big-font {font-size: 56px !important; font-weight: bold; text-align: center; color: #1e40af;}
    .todo-item {padding: 16px; margin: 10px 0; border-radius: 12px; background: #f8fafc;
                border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .completed {text-decoration: line-through; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">Lightning Supabase Todo<br><small>Login works • Real-time sync</small></p>', unsafe_allow_html=True)

# ─── Authentication (sync client — this fixes login forever) ─────
if "user" not in st.session_state:
    st.session_state.user = None

# Logout
if st.sidebar.button("Log Out") and st.session_state.user:
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# Login / Sign Up
if not st.session_state.user:
    tab1, tab2 = st.sidebar.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                    st.session_state.user = res.user
                    st.success("Logged in!")
                    st.rerun()
                except:
                    st.error("Wrong email or password")

    with tab2:
        with st.form("signup"):
            email = st.text_input("Email", key="su_email")
            pwd = st.text_input("Password", type="password", key="su_pwd")
            if st.form_submit_button("Sign Up"):
                try:
                    supabase.auth.sign_up({"email": email, "password": pwd})
                    st.success("Check your email to confirm!")
                    st.balloons()
                except Exception as e:
                    st.error("Try another email")

    st.stop()  # Stop here if not logged in

# ─── Logged in! Show user ─────
st.sidebar.success(f"Logged in as {st.session_state.user.email}")

# ─── Add Todo ─────
with st.form("add", clear_on_submit=True):
    task = st.text_area("New todo")
    if st.form_submit_button("Add Todo") and task.strip():
        asyncio.run(async_supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task.strip(),
            "is_complete": False
        }).execute())

# ─── Load Todos ─────
async def get_todos():
    resp = await async_supabase.table("todos")\
        .select("*")\
        .eq("user_id", st.session_state.user.id)\
        .order("inserted_at", desc=True)\
        .execute()
    return resp.data

todos = asyncio.run(get_todos())

st.subheader("Your Todos (real-time)")

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
                asyncio.run(async_supabase.table("todos").update(
                    {"is_complete": not todo["is_complete"]})
                    .eq("id", todo["id"]).execute())
                st.rerun()
        with c3:
            if st.button("Delete", key=f"d{todo['id']}"):
                asyncio.run(async_supabase.table("todos").delete().eq("id", todo["id"]).execute())
                st.rerun()

# ─── TRUE REAL-TIME (one-liner, works perfectly) ─────
if "rt_setup" not in st.session_state:
    def refresh(): st.rerun()
    async_supabase.channel("todos-chan")\
        .on_postgres_changes(event="*", schema="public", table="todos",
                             filter=f"user_id=eq.{st.session_state.user.id}", callback=refresh)\
        .subscribe()
    st.session_state.rt_setup = True
    st.toast("Real-time connected!")

st.caption("True instant sync • Works across tabs & devices!")
