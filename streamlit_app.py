# At the top of streamlit_app.py, after imports
import streamlit as st
from st_supabase_connection import SupabaseConnection

# Initialize via st.connection (secrets handled automatically)
@st.cache_resource
def init_supabase():
    return st.connection("supabase", type=SupabaseConnection)

supabase = init_supabase()