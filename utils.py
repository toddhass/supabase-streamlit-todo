# utils.py
import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Missing Supabase credentials")
        st.stop()
    return create_client(url, key)

supabase: Client = get_supabase()
