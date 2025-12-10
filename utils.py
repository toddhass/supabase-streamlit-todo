# utils.py
import os
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Missing Supabase credentials – check secrets or .env")
        st.stop()
    return create_client(url, key)

supabase: Client = init_supabase()

def get_current_user():
    try:
        session = supabase.auth.get_session()
        return session.user if session and session.user else None
    except:
        return None
