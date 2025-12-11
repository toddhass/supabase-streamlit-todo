# streamlit_app.py ← ASYNC REALTIME VERSION (FIXES LINE 63 ERROR)
import streamlit as st
from supabase import acreate_client  # Use async client for realtime
import asyncio

# --- Async Supabase Client ---
@st.cache_resource
async def get_supabase_async():
    return await acreate_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Global client (initialized once)
if "supabase" not in st.session_state:
    st.session_state.supabase = asyncio.run(get_supabase_async())
supabase = st.session_state.supabase

# --- Load Todos (Synchronous for compatibility) ---
def load_todos(user_id):
    try:
        # Use sync RPC for loading (compatible with async client)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resp = loop.run_until_complete(
            supabase.rpc("get_user_todos", {"target_user_id": str(user_id), "status_filter": "All Tasks"}).execute()
        )
        loop.close()
        return resp.data or []
    except Exception as e:
        st.error(f"Load error: {e}")
        return []

# --- Handlers (no st.rerun() — realtime will trigger) ---
def add_todo(task):
    if task.strip():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            supabase.table("todos").insert({
                "user_id": st.session_state.user.id,
                "task": task.strip(),
                "is_complete": False
            }).execute()
        )
        loop.close()

def toggle(todo_id, current):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        supabase.table("todos").update({"is_complete": not current}).eq("id", todo_id).execute()
    )
    loop.close()

def delete_todo(todo_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        supabase.table("todos").delete().eq("id", todo_id).execute()
    )
    loop.close()

def logout():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(supabase.auth.sign_out())
    loop.close()
    st.session_state.user = None
    st.rerun()

# --- Async Realtime Subscription ---
async def setup_realtime(user_id):
    channel = supabase.channel("todos-changes")
    def callback(payload):
        st.session_state["realtime_trigger"] = True

    # Subscribe to Postgres changes
    channel.on_postgres_changes(
        event="*",
        schema="public",
        table="todos",
        filter=f"user_id=eq.{user_id}",
        callback=callback
    )
    await channel.subscribe()

# --- Page Setup ---
st.set_page_config(page_title="My Todos", page_icon="📝", layout="centered")
st.title("My Todos")

# --- Authentication Check ---
if "user" not in st.session_state:
    st.session_state.user = None

try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sess = loop.run_until_complete(supabase.auth.get_session())
    loop.close()
    if sess and sess.user:
        st.session_state.user = sess.user
except:
    pass

user = st.session_state.user

if user:
    # Setup realtime (run async setup once)
    if "realtime_setup" not in st.session_state:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_realtime(user.id))
        loop.close()
        st.session_state.realtime_setup = True
        st.session_state.realtime_trigger = False

    st.button("Log out", on_click=logout)

    # Add Todo Form
    with st.form("add_todo_form", clear_on_submit=True):
        new_task = st.text_input("New Todo")
        submitted = st.form_submit_button("Add")
        if submitted:
            add_todo(new_task)

    # Load and Display Todos
    todos = load_todos(user.id)

    if not todos:
        st.info("No todos yet — add one above!")
    else:
        # Render in Table Format
        table_data = []
        for todo in todos:
            row = {
                "Task": todo["task"],
                "Completed": st.checkbox("Completed", value=todo["is_complete"], key=f"chk_{todo['id']}", on_change=toggle, args=(todo["id"], todo["is_complete"])),
                "Delete": st.button("Delete", key=f"del_{todo['id']}", on_click=delete_todo, args=(todo["id"],))
            }
            table_data.append(row)
        st.table(table_data)

    # Trigger rerun on realtime change
    if st.session_state.get('realtime_trigger', False):
        st.session_state.realtime_trigger = False
        st.rerun()

else:
    # Login/Signup
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    resp = loop.run_until_complete(supabase.auth.sign_in_with_password({"email": email, "password": password}))
                    loop.close()
                    if resp.user:
                        st.session_state.user = resp.user
                        st.success("Logged in!")
                        st.rerun()
                except Exception as e:
                    st.error("Wrong email or password.")

    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                if len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(supabase.auth.sign_up({"email": email, "password": password}))
                        loop.close()
                        st.success("Success! Check your email to confirm.")
                    except Exception as e:
                        st.error("Email already exists or invalid.")

    st.stop()