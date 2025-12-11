# streamlit_app.py ← UPDATED WITH UI IMPROVEMENTS AND FIXES
import streamlit as st
from supabase import create_client
from streamlit_js_eval import streamlit_js_eval

# --- Supabase Client & Function Definitions ---
@st.cache_resource
def get_supabase():
    # Only cache the expensive client creation resource
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# 🛑 RPC Stability Fix: Ensuring a list is always returned 🛑
def load_todos(_user_id):
    """Loads all todos for the current user using an RPC to bypass the broken client sorting."""
    
    # We pass the user ID and fixed filter string directly to the database function.
    params = {
        "target_user_id": str(_user_id),
        "status_filter": "All Tasks"
    }

    try:
        # Use rpc() to call the PostgreSQL function 'get_user_todos'.
        response = supabase.rpc("get_user_todos", params=params).execute()
        
        # FINAL STABILITY FIX: Ensure response.data is a list.
        data = response.data
        if data is None:
            return []  # Return empty list if None is returned
            
        return data
            
    except Exception as e:
        # A defensive return
        st.error(f"Failed to load todos: {str(e)}")  # Simplified error message for better UX
        return []

# --- Handlers (Updated for Confirmation) ---
def update_todo_status(todo_id, new_status):
    """Handles the change of the checkbox status."""
    supabase.table("todos").update({"is_complete": new_status})\
        .eq("id", todo_id).execute()
    st.rerun()

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
        st.rerun()
    else:
        pass
        
def delete_todo(todo_id):
    """Handles todo deletion with confirmation."""
    supabase.table("todos").delete().eq("id", todo_id).execute()
    st.rerun()

def logout():
    """Handles the log out process."""
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- Modular Function for Rendering Todo Items ---
def render_todo_item(todo, col_ratios):
    """Renders a single todo item with checkbox and delete confirmation."""
    completed = todo.get("is_complete", False)
    
    wrapper_class = "completed-todo" if completed else ""
    
    with st.container(border=False):
        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)

        # Column structure