# streamlit_app.py ← FINAL, BUTTONS SIDE-BY-SIDE VERSION
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

def add_todo_callback():
    """Handles todo insertion and safely clears the input field state."""
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

# --- 💅 Custom CSS (Aggressive Resets for Alignment) ---
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

    /* Target the container holding the columns for the card look */
    div[data-testid="stVerticalBlock"] > div:has([data-testid="stHorizontalBlock"]) > div {
        background: var(--card-bg);
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.06);
        border-left: 5px solid var(--primary-color);
        transition: all 0.2s ease-in-out;
        padding: 0.5rem 1rem;
    }
    
    /* ALIGNMENT FIX 1: Vertical centering for the columns */
    div[data-testid="stHorizontalBlock"] {
        display: flex;
        align-items: center; 
    }
    
    /* ALIGNMENT FIX 2: Aggressively remove padding/margin from elements inside the column containers */
    div[data-testid="stHorizontalBlock"] > div[data-testid*="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Styling for completed state */
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
    /* Ensure buttons inside sub-columns take up the space evenly */
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

    # --- Show Todos (Layout Guaranteed - BUTTONS FIXED) ---
    st.markdown(f"### Your Todos <span class='live'>LIVE</span>", unsafe_allow_html=True)

    if not todos:
        st.info("No todos yet — add one above!")
    else:
        for todo in todos:
            completed = todo.get("is_complete", False)
            
            wrapper_class = "completed-todo" if completed else ""
            
            with st.container(border=False):
                st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)

                # 1. Use two main columns: c1 for task, c2 for both buttons (merged)
                c1, c2_merged = st.columns([5, 3]) 
                
                with c1:
                    text_class = "completed-text" if completed else ""
                    task_html = f'<span class="task-text {text_class}">{todo["task"]}</span>'
                    st.markdown(task_html, unsafe_allow_html=True) 

                with c2_merged:
                    # 2. NEST two columns inside the merged column for the buttons
                    btn_col_done, btn_col_remove = st.columns(2)
                    
                    with btn_col_done:
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
                    
                    with btn_col_remove:
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
