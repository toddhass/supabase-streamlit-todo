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
        
        # FINAL STABILITY FIX