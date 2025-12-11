# streamlit_app.py ← FINAL, SINGLE-CLICK LOGIN FIX
import streamlit as st
from supabase import create_client
# Removed time import as sleep is no longer needed

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

# --- Handlers (No change here) ---
def update_todo_status(todo_id, new_status):
    """Handles the change of the toggle status."""
    supabase.table("todos").update({"is_complete": new_status})\
        .eq("id", todo_id).execute()
    st.cache_data.clear()

def handle_add_todo(task_to_add):
    """Handles todo insertion logic."""
    if "user" not in st.session_state or not st.session_state.user:
        return

    if task_to_add.strip():
        supabase.table("todos").insert({
            "user_id": st.session_state.user.id,
            "task": task_to_add.strip(),
            "is_complete": False
        }).execute()

        st.cache_data.clear()
    else:
        pass
        
def logout():
    """Handles the log out process."""
    supabase.auth.sign_out()
    st.session_state.user = None
    st.cache_data.clear()
    st.rerun()


# --- Page Setup ---
st.set_page_config(page_title="My Todos", page_icon="📝", layout="centered")

# --- 💅 Custom CSS (No change) ---
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
    .stButton > button { height: 38px; }
    .stButton button[kind="secondary"] { border-color: var(--danger-color); color: var(--danger-color); }
    .stButton button[kind="primary"] { background-color: var(--primary-color); border-color: var(--primary-color); }

    /* Fix for st.toggle: ensures it aligns vertically well */
    div[data-testid="stToggle"] {
        padding-top: 4px; 
    }
    
    /* NEW LOGOUT BLOCK STYLING */
    .user-info-block {
        background: #ecfdf5; 
        padding: 8px 15px; 
        border-radius: 8px;
        border: 1px solid #a7f3d0;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between; 
        align-items: center;
        font-size: 0.95rem;
    }
    .logout-link {
        color: var(--danger-color); 
        text-decoration: underline;
        font-weight: 600;
        cursor: pointer;
    }
    .logged-in-email {
        font-weight: 600;
        color: var(--primary-color);
    }

</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">My Modern Todos</h1>', unsafe_allow_html=True)
st.caption("Real-time • Instant sync • Powered by Supabase")

# --- Authentication Check (Standard Flow) ---
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
    
    # Clean, one-line status and logout link
    with st.container(border=False):
        st.markdown(
            f"""
            <div class="user-info-block">
                <span>Logged in as <span class="logged-in-email">{user.email}</span></span>
                <span style="float: right;">
            """, unsafe_allow_html=True
        )
        st.button(
            "Log out", 
            on_click=logout, 
            key="logout_link_btn",
            type="secondary",
            use_container_width=False
        )
        st.markdown(
            """
                </span>
            </div>
            """, unsafe_allow_html=True
        )
    
    # Load todos
    todos = load_todos(user.id) 

    # --- Add Todo (Using st.form to prevent duplicate submissions) ---
    st.markdown("### Add a new todo")

    with st.form("add_todo_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        
        with col_input:
            new_task = st.text_input(
                "What needs to be done?", 
                placeholder="e.g., Deploy modern UI changes", 
                label_visibility="collapsed", 
                key="task_input_in_form"
            )
        
        with col_btn:
            submitted = st.form_submit_button(
                "Add", 
                type="primary", 
                use_container_width=True
            )
        
        if submitted:
            handle_add_todo(new_task)
            st.rerun() 

    # --- Show Todos (st.toggle Implemented) ---
    st.markdown(f"### Your Todos <span class='live'>LIVE</span>", unsafe_allow_html=True)

    if not todos:
        st.info("No todos yet — add one above!")
    else:
        for todo in todos:
            completed = todo.get("is_complete", False)
            
            wrapper_class = "completed-todo" if completed else ""
            
            with st.container(border=False):
                st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)

                # Column structure
                c_toggle, c_task, c_remove = st.columns([1.5, 6.5, 1.5]) 
                
                with c_toggle:
                    # Native Streamlit Toggle for status
                    st.toggle(
                        label="Completed", 
                        value=completed, 
                        key=f"toggle_{todo['id']}",
                        on_change=update_todo_status,
                        args=(todo["id"], not completed)
                    )

                with c_task:
                    # Task Text
                    text_class = "completed-text" if completed else ""
                    task_html = f'<span class="task-text {text_class}">{todo["task"]}</span>'
                    st.markdown(task_html, unsafe_allow_html=True) 

                with c_remove:
                    # Single Remove Button
                    if st.button("Remove", key=f"del_{todo['id']}", use_container_width=True, type="secondary"):
                        # Instant removal logic
                        supabase.table("todos").delete().eq("id", todo["id"]).execute()
                        st.cache_data.clear()
                        st.rerun() 
                        
                st.markdown("</div>", unsafe_allow_html=True) 

    pass

else:
    # ----------------------------------------------------
    # NOT LOGGED IN CONTENT (Login and Sign Up Tabs)
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
                        # 1. Attempt Sign-In
                        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        
                        # 2. FIX: Immediately update session state with the new user object
                        if response and response.user:
                            st.session_state.user = response.user
                            st.success("Logged in! Redirecting...")
                            st.rerun() 
                        else:
                            # Handle cases where sign-in succeeds but user object is not immediately available (rare, but safe)
                            raise Exception("Login response incomplete.")
                            
                    except Exception as e:
                        # Check the actual error message if needed, but display a generic error
                        st.error("Wrong email or password or connection issue.")
                        
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
