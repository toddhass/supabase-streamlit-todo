# streamlit_app.py ← FINAL, MODERNIZED, AND USER-FRIENDLY VERSION
import streamlit as st
from supabase import create_client
import time

# --- Supabase Client ---
@st.cache_resource
def get_supabase():
    # Ensure SUPABASE_URL and SUPABASE_KEY are in your .streamlit/secrets.toml
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# --- Page Setup ---
st.set_page_config(page_title="My Todos", page_icon="📝", layout="centered")

# --- 💅 Modernized CSS for a cleaner, more appealing UI ---
st.markdown("""
<style>
    /* Color Variables for easy theme adjustment (Tailwind-inspired) */
    :root {
        --primary-color: #10b981; /* Emerald Green/Teal */
        --secondary-color: #3b82f6; /* Soft Blue */
        --danger-color: #ef4444; /* Red */
        --bg-light: #f9fafb; /* Subtle off-white for body */
        --card-bg: white;
        --text-muted: #6b7280;
    }
    
    /* Apply background to the main page content */
    div.stApp {background-color: var(--bg-light);}

    /* Main Title Styling */
    .big-title {
        font-size: 4.5rem !important;
        font-weight: 900;
        text-align: center;
        /* Updated Gradient */
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
        /* Modern, subtle box shadow */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.06);
        border-left: 5px solid var(--primary-color);
        transition: all 0.2s ease-in-out;
    }

    /* Completed State Styling */
    .completed {
        opacity: 0.85; 
        background: #f1f5f9; /* Subtle light gray */
        border-left-color: #94a3b8; /* Subtle gray border */
    }
    
    /* Apply line-through only to the task text when completed */
    .completed .task-text { 
        text-decoration: line-through; 
        color: var(--text-muted); /* Muted color for completed text */
    }
    
    /* LIVE Badge */
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
        height: 38px; /* Match input height for alignment */
    }

    /* Custom style for the DELETE button (secondary but red) */
    .stButton button[kind="secondary"] {
        border-color: var(--danger-color);
        color: var(--danger-color);
    }
    /* Ensure the "Done" button is the primary green */
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

# --- Add Todo (Integrated Input) ---
st.markdown("### Add a new todo")
with st.container():
    col_input, col_btn = st.columns([5, 1])
    
    with col_input:
        task = st.text_input(
            "What needs to be done?", 
            placeholder="e.g., Deploy modern UI changes", 
            label_visibility="collapsed", 
            key="task_input"
        )
    
    with col_btn:
        if st.button("Add", type="primary", use_container_width=True):
            if task.strip():
                supabase.table("todos").insert({
                    "user_id": user.id,
                    "task": task.strip(),
                    "is_complete": False
                }).execute()
                st.cache_data.clear()
                st.rerun()
            else:
                 st.error("Task cannot be empty.")

# --- Show Todos (Clear Button Labels) ---
st.markdown(f"### Your Todos <span class='live'>LIVE</span>", unsafe_allow_html=True)

if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        completed = todo.get("is_complete", False)
        
        with st.container():
            st.markdown(f'<div class="todo-card {"completed" if completed else ""}">', unsafe_allow_html=True)
            
            # Column ratios: Task | Done/Redo Button | Remove Button
            c1, c2, c3 = st.columns([5, 1.5, 1.5]) 
            
            with c1:
                # Use the custom CSS class 'task-text' for styling
                st.markdown(f'<h5 class="task-text">{todo["task"]}</h5>', unsafe_allow_html=True) 

            with c2:
                # Clear, descriptive text labels for the toggle
                if completed:
                    button_label = "Redo" 
                    button_type = "secondary" # Uses default grey style
                else:
                    button_label = "Done"
                    button_type = "primary" # Uses primary (green) style

                if st.button(button_label, key=f"tog_{todo['id']}", use_container_width=True, type=button_type):
                    supabase.table("todos").update({"is_complete": not completed})\
                        .eq("id", todo["id"]).execute()
                    st.cache_data.clear()
                    st.rerun()
            
            with c3:
                # Use "Remove" label, which is styled red via CSS in 'secondary'
                if st.button("Remove", key=f"del_{todo['id']}", use_container_width=True, type="secondary"):
                    supabase.table("todos").delete().eq("id", todo["id"]).execute()
                    st.cache_data.clear()
                    st.rerun()
                    
            st.markdown("</div>", unsafe_allow_html=True)

# --- Auto-refresh ---
time.sleep(3)
st.rerun()
