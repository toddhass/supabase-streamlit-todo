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
def load_todos(_user_id, status_filter):
    """Loads todos for the current user using an RPC to bypass the broken client sorting."""
    
    # We pass the user ID and the filter string directly to the database function.
    params = {
        "target_user_id": str(_user_id),
        "status_filter": status_filter
    }

    try:
        # Use rpc() to call the PostgreSQL function 'get_user_todos'.
        response = supabase.rpc("get_user_todos", params=params).execute()
        
        # FINAL STABILITY FIX: Ensure response.data is a list.
        data = response.data
        if data is None:
            return [] # Return empty list if None is returned
            
        return data
            
    except Exception as e:
        # A defensive return
        st.error(f"Failed to load todos: {str(e)}")  # Simplified error message for better UX