# streamlit_app.py ← FINAL, FIXED, AND CORRECTLY BEHAVED VERSION
import streamlit as st
from supabase import create_client
import time

# --- Supabase Client ---
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# --- CALLBACK FUNCTION FOR ADDING TODO ---
def add_todo_callback():
    """Handles todo insertion and clears the input field state."""
    # Ensure user is logged in before proceeding
    if "user" not in st.session_state or not st.session_state.user:
        return

    task_to_add = st.session_state.task_input
    
    if task_to_add.strip():
        # 1. Insert the todo
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task_to_add.strip(),
            "is_complete": False
        }).execute()

        # 2. Clear the input field's state (SAFE INSIDE CALLBACK)
        st.session_state.task_input = "" 
        
        # 3. Clear the cache (A rerun will automatically follow this callback)
        st.cache_data.clear()
    else:
        # Optional: You could show a transient error message here if needed
        pass

# --- Page Setup ---
st.set_page_config(page_title="My Todos", page_icon="📝", layout="centered")

# --- 💅 Modernized CSS ---
st.markdown("""
<style>
    /* Color Variables */
    :root {
        --primary-color: #10b981; 
        --secondary-color: #3b82f6; 
        --danger-color: #ef4444; 
        --bg-light: #f9fafb; 
        --card-bg: white;
        --text-muted: #6b7280;
    }
    
    div.stApp {background-color: var(--bg-light);}

    .big-title {
        font-size: 4.5rem !important;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, var(--secondary-color) 0%, var(--primary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    /* Modern Todo Card Styling */
    .todo-card {
        background: var(--card-bg);
        padding: 1.5rem; 
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.06);
        border-left: 5px solid var(--primary-color);
        transition: all 0.2s ease-in-out;
    }

    .completed {
        opacity: 0.85; 
        background: #f1f5f9; 
        border-left-color: #94a3b8; 
    }
    
    .completed .task-text { 
        text-decoration: line-through; 
        color: var(--text-muted); 
    }
    
    .live {
        background: var(--primary-color);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        vertical-align: middle;
        margin-left: 10px;
    }

    /* Button Customization */
    .stButton > button {
        height: 38px; 
    }

    /* Custom style for the DELETE button (secondary but red) */
    .stButton button[kind="secondary"] {
        border-color: var(--danger-color);
        color: var(--danger-color);
    }
    .stButton button[kind="primary"] {
        background-color: var(--primary-color); 
        border-color: var(--primary-color);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">My Modern Todos</h1>', unsafe_allow_html=True)
st.caption("Real-time • Instant sync • Powered by Supabase")

# --- Authentication ---
if "user" not in st.session_state:
    st.session_state.user = None

try:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.user = session.user
except:
    pass

user = st.session_state.user

if user:
    col1, col2 = st.columns([6,1])
    with col2:
        if st.button("Log out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
    st.success(f"Logged in as **{user.email}**")
else:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.form_submit_button("Log In", type="primary", use_container_width=True):
                if not email or not password:
                    st.error("Please enter both fields")
                else:
                    try:
                        supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.success("Logged in! Redirecting...")
                        st.rerun()
                    except:
                        st.error("Wrong email or password")

    with tab2:
        with st.form("signup_form", clear_on_submit=False):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            if st.form_submit_button("Sign Up", type="primary", use_container_width=True):
                if len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Success! Check your email to confirm.")
                        st.balloons()
                    except Exception as e:
                        st.error("Email already exists or invalid.")

    st.stop()

# --- Load Todos ---
@st.cache_data(ttl=2, show_spinner=False)
def load_todos(_user_id):
    return supabase.table("todos")\
        .select("*")\
        .eq("user_id", _user_id)\
        .order("id", desc=True)\
        .execute().data

todos = load_todos(user.id)

# --- Add Todo (Integrated Input with Callback) ---
st.markdown("### Add a new todo")

# Initialize the state key for task input
if "task_input" not in st.session_state:
    st.session_state.task_input = "" 
    
with st.container():
    col_input, col_btn = st.columns([5, 1])
    
    with col_input:
        # Input field is linked to st.session_state.task_input via key
        st.text_input(
            "What needs to be done?", 
            placeholder="e.g., Deploy modern UI changes", 
            label_visibility="collapsed", 
            key="task_input"
        )
    
    with col_btn:
        # Use the callback function to safely submit and clear the input
        st.button(
            "Add", 
            type="primary", 
            use_container_width=True,
            on_click=add_todo_callback # <-- THE SAFE WAY TO RESET STATE
        )

# --- Show Todos (Clear Button Labels) ---
st.markdown(f"### Your Todos <span class='live'>LIVE</span>", unsafe_allow_html=True)

if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        completed = todo.get("is_complete", False)
        
        with st.container():
            st.markdown(f'<div class="todo-card {"completed" if completed else ""}">', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([5, 1.5, 1.5]) 
            
            with c1:
                st.markdown(f'<h5 class="task-text">{todo["task"]}</h5>', unsafe_allow_html=True) 

            with c2:
                if completed:
                    button_label = "Redo" 
                    button_type = "secondary" 
                else:
                    button_label = "Done"
                    button_type = "primary" 

                if st.button(button_label, key=f"tog_{todo['id']}", use_container_width=True, type=button_type):
                    supabase.table("todos").update({"is_complete": not completed})\
                        .eq("id", todo["id"]).execute()
                    st.cache_data.clear()
                    st.rerun()
            
            with c3:
                if st.button("Remove", key=f"del_{todo['id']}", use_container_width=True, type="secondary"):
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()
                    st.cache_data.clear()
                    st.rerun()
                    
            st.markdown("</div>", unsafe_allow_html=True)

# --- Auto-refresh ---
time.sleep(3)
st.rerun()
