# streamlit_app.py ← FINAL, TOGGLE SWITCH UI
import streamlit as st
from supabase import create_client
import time

# --- Supabase Client & Function Definitions ---
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=2, show_spinner=False)
def load_todos(_user_id):
    """Loads todos for the current user."""
    return supabase.table("todos")\
        .select("*")\
        .eq("user_id", _user_id)\
        .order("id", desc=True)\
        .execute().data

# --- Checkbox/Toggle Update Handler ---
def update_todo_status(todo_id, new_status):
    """Handles the change of the toggle status."""
    supabase.table("todos").update({"is_complete": new_status})\
        .eq("id", todo_id).execute()
    st.cache_data.clear()

def add_todo_callback():
    """Handles todo insertion and clears the input field state."""
    if "user" not in st.session_state or not st.session_state.user:
        return

    task_to_add = st.session_state.task_input
    
    if task_to_add.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task_to_add.strip(),
            "is_complete": False
        }).execute()

        st.session_state.task_input = "" 
        st.cache_data.clear()
    else:
        pass

# --- Page Setup ---
st.set_page_config(page_title="My Todos", page_icon="📝", layout="centered")

# --- 💅 Custom CSS (TOGGLE SWITCH IMPLEMENTATION) ---
st.markdown("""
<style>
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

    /* Card Styling */
    div[data-testid="stVerticalBlock"] > div:has([data-testid="stHorizontalBlock"]) > div:not(.header-row) {
        background: var(--card-bg);
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.06);
        border-left: 5px solid var(--primary-color);
        transition: all 0.2s ease-in-out;
        padding: 0.5rem 1rem;
    }
    
    /* Layout Alignment */
    div[data-testid="stHorizontalBlock"] {
        display: flex;
        align-items: center; 
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid*="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Completed State Styling */
    .completed-todo div[data-testid="stHorizontalBlock"] {
        opacity: 0.85; 
        background: #f1f5f9; 
        border-left-color: #94a3b8; 
    }
    
    /* Task Text Styling */
    .task-text {
        font-weight: 600;
        margin: 0;
        padding: 0;
        display: block;
        font-size: 1rem;
        line-height: 1.5rem;
    }
    .completed-text { 
        text-decoration: line-through; 
        color: var(--text-muted); 
    }
    
    /* Header Text Styling */
    .header-text {
        font-weight: 700;
        font-size: 0.9rem;
        color: #374151;
    }

    /* 🛑 TOGGLE SWITCH CSS TRANSFORMATION 🛑 */
    /* Target the checkbox container and hide the default element */
    div[data-testid="stCheckbox"] label {
        display: flex;
        align-items: center;
        /* Position the input to be invisible but clickable */
    }
    
    div[data-testid="stCheckbox"] input[type="checkbox"] {
        /* Hide native checkbox */
        opacity: 0;
        width: 0;
        height: 0;
    }

    /* Create the visual slider track */
    div[data-testid="stCheckbox"] label::before {
        content: "";
        position: relative;
        cursor: pointer;
        width: 40px; /* Toggle width */
        height: 20px; /* Toggle height */
        background-color: #ccc;
        border-radius: 20px;
        transition: 0.4s;
        margin-right: 8px; /* Space between toggle and task text */
    }

    /* Create the visual slider handle (the circle) */
    div[data-testid="stCheckbox"] label::after {
        content: "";
        position: absolute;
        left: 2px; /* Starting position of handle */
        top: 2px;
        width: 16px; /* Handle size */
        height: 16px;
        background-color: white;
        border-radius: 50%;
        transition: 0.4s;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
    }
    
    /* Checked state: Track color and Handle position */
    div[data-testid="stCheckbox"] input:checked + div > label::before {
        background-color: var(--primary-color);
    }

    div[data-testid="stCheckbox"] input:checked + div > label::after {
        transform: translateX(20px); /* Move handle to the right (40px width - 2px padding * 2 - 16px handle = 20px shift) */
    }

    /* Final fix for Streamlit's internal checkbox structure (if needed) */
    div[data-testid="stCheckbox"] > label {
        padding-top: 5px; /* Adjust top padding for vertical alignment */
    }

    /* Remove the default label text that Streamlit adds */
    div[data-testid="stCheckbox"] > label > div:nth-child(2) {
        display: none;
    }

    /* Button Customization (Remove button only) */
    .stButton > button { height: 38px; }
    .stButton button[kind="secondary"] { border-color: var(--danger-color); color: var(--danger-color); }
    .stButton button[kind="primary"] { background-color: var(--primary-color); border-color: var(--primary-color); }

</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">My Modern Todos</h1>', unsafe_allow_html=True)
st.caption("Real-time • Instant sync • Powered by Supabase")

# --- Authentication Check ---
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
    # ----------------------------------------------------
    # LOGGED IN USER CONTENT
    # ----------------------------------------------------
    
    col1, col2 = st.columns([6,1])
    with col2:
        if st.button("Log out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.cache_data.clear()
            st.rerun()
    st.success(f"Logged in as **{user.email}**")

    # Load todos
    todos = load_todos(user.id) 

    # --- Add Todo (Integrated Input with Callback) ---
    st.markdown("### Add a new todo")

    if "task_input" not in st.session_state:
        st.session_state.task_input = "" 
        
    with st.container():
        col_input, col_btn = st.columns([5, 1])
        
        with col_input:
            st.text_input(
                "What needs to be done?", 
                placeholder="e.g., Deploy modern UI changes", 
                label_visibility="collapsed", 
                key="task_input"
            )
        
        with col_btn:
            st.button(
                "Add", 
                type="primary", 
                use_container_width=True,
                on_click=add_todo_callback 
            )

    # --- Show Todos (Toggle Implemented) ---
    st.markdown(f"### Your Todos <span class='live'>LIVE</span>", unsafe_allow_html=True)

    # 🛑 HEADER ROW: Labels for the columns
    with st.container(border=False):
        st.markdown('<div class="header-row">', unsafe_allow_html=True)
        # Use the same column ratios: [Toggle size, Task size, Button size]
        h_toggle, h_task, h_remove = st.columns([0.5, 7.5, 1.5])
        
        with h_toggle:
            st.markdown('<p class="header-text" style="text-align: center;">DONE</p>', unsafe_allow_html=True)
        with h_task:
            st.markdown('<p class="header-text">TASK DESCRIPTION</p>', unsafe_allow_html=True)
        with h_remove:
            st.markdown('<p class="header-text">ACTIONS</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    # -----------------------------------------------------------------

    if not todos:
        st.info("No todos yet — add one above!")
    else:
        for todo in todos:
            completed = todo.get("is_complete", False)
            
            wrapper_class = "completed-todo" if completed else ""
            
            with st.container(border=False):
                st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)

                # 1. Use columns matching the header structure
                c_toggle, c_task, c_remove = st.columns([0.5, 7.5, 1.5]) 
                
                with c_toggle:
                    # 2. Checkbox transformed into a toggle switch
                    st.checkbox(
                        label="", 
                        value=completed, 
                        key=f"toggle_{todo['id']}",
                        label_visibility="hidden",
                        on_change=update_todo_status,
                        args=(todo["id"], not completed)
                    )

                with c_task:
                    # 3. Task Text
                    text_class = "completed-text" if completed else ""
                    task_html = f'<span class="task-text {text_class}">{todo["task"]}</span>'
                    st.markdown(task_html, unsafe_allow_html=True) 

                with c_remove:
                    # 4. Single Remove Button
                    if st.button("Remove", key=f"del_{todo['id']}", use_container_width=True, type="secondary"):
                        supabase.table("todos").delete().eq("id", todo["id"]).execute()
                        st.cache_data.clear()
                        st.rerun()
                        
                st.markdown("</div>", unsafe_allow_html=True) 

    # --- Auto-refresh ---
    time.sleep(3)
    st.rerun()

else:
    # ----------------------------------------------------
    # NOT LOGGED IN CONTENT
    # ----------------------------------------------------
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
