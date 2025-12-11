# streamlit_app.py ← ASYNCHRONOUS REAL-TIME VERSION (December 2025)
import streamlit as st
import asyncio
from supabase import acreate_client, AsyncClient

# ─── Asynchronous Supabase client ─────────────────────
@st.cache_resource
def init_supabase():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(acreate_supabase())

async def acreate_supabase() -> AsyncClient:
    return await acreate_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: AsyncClient = init_supabase()

st.set_page_config(page_title="My Todos", page_icon="Checkmark", layout="centered")

# ─── Styling ─────────────────────
st.markdown("""
<style>
    .big-title {font-size:4.5rem!important;font-weight:900;text-align:center;
                background:linear-gradient(90deg,#667eea 0%,#764ba2 100%);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
    .todo-card {background:white;padding:1.8rem;margin:1.2rem 0;border-radius:18px;
                box-shadow:0 12px 40px rgba(0,0,0,.12);border-left:7px solid #667eea;}
    .completed {opacity:0.65;text-decoration:line-through;background:#f8f9fa;border-left-color:#28a745;}
    .live {background:#10b981;color:white;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.8rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">Checkmark My Todos</h1>', unsafe_allow_html=True)
st.caption("Real-time • Instant sync • Powered by Supabase")

# ─── Authentication (synchronous fallback via sync wrapper) ─────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    session = loop.run_until_complete(supabase.auth.get_session())
    if session and session.user:
        st.session_state.user = session.user
except:
    pass

user = st.session_state.user

if user:
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Log out"):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(supabase.auth.sign_out())
            st.session_state.user = None
            st.rerun()
    st.success(f"Logged in as **{user.email}**")
else:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Log In", type="primary"):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(supabase.auth.sign_in_with_password({"email": email, "password": pw}))
                    st.rerun()
                except:
                    st.error("Wrong credentials")

    with tab2:
        with st.form("signup"):
            email = st.text_input("Email", key="su_email")
            pw = st.text_input("Password", type="password", key="su_pw")
            if st.form_submit_button("Sign Up", type="primary"):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(supabase.auth.sign_up({"email": email, "password": pw}))
                    st.success("Check your email to confirm!")
                    st.balloons()
                except:
                    st.error("Sign-up failed")

    st.stop()

# ─── Load todos once ─────────────────────
if "todos" not in st.session_state:
    def load():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resp = loop.run_until_complete(supabase.table("todos").select("*").eq("user_id", user.id).order("id", desc=True).execute())
        st.session_state.todos = resp.data or []
    load()

# ─── Real-time subscription (async background task) ─────────────────────
if "realtime_task" not in st.session_state:
    async def realtime_listener():
        try:
            channel = supabase.channel("todos-changes")\
                .on_postgres_changes(
                    event="*", schema="public", table="todos",
                    filter=f"user_id=eq.{user.id}"
                )\
                .on("postgres_changes", lambda payload: st.rerun())
            await channel.subscribe()
        except Exception as e:
            st.warning(f"Realtime setup failed: {str(e)}. Falling back to polling.")
            # Fallback polling
            while True:
                await asyncio.sleep(5)
                load()
                st.rerun()

    st.session_state.realtime_task = asyncio.create_task(realtime_listener())

# ─── Add todo ─────────────────────
st.markdown("### Checkmark Add a new todo")
with st.form("add_todo", clear_on_submit=True):
    task = st.text_area("What needs to done?", height=100, label_visibility="collapsed")
    if st.form_submit_button("Add Todo Checkmark", type="primary", use_container_width=True):
        if task.strip():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(supabase.table("todos").insert({
                "user_id": user.id,
                "task": task.strip(),
                "is_complete": False
            }).execute())
            st.success("Added instantly!")
            st.balloons()

# ─── Show todos ─────────────────────
st.markdown(f"### Checkmark Your Todos <span class='live'>LIVE</span>", unsafe_allow_html=True)

if not st.session_state.todos:
    st.info("No todos yet — add one above!")
else:
    for todo in st.session_state.todos:
        completed = todo.get("is_complete", False)
        with st.container():
            st.markdown(f'<div class="todo-card {"completed" if completed else ""}">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([6, 2, 2])
            with c1:
                icon = "Checkmark" if completed else "Circle"
                st.markdown(f"### {icon} **{todo['task']}**")
            with c2:
                if st.button("Toggle", key=f"tog_{todo['id']}"):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(supabase.table("todos").update({"is_complete": not completed}).eq("id", todo["id"]).execute())
            with c3:
                if st.button("Delete", key=f"del_{todo['id']}", type="secondary"):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(supabase.table("todos").delete().eq("id", todo["id"]).execute())
            st.markdown("</div>", unsafe_allow_html=True)