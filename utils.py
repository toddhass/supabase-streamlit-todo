# utils.py
import os
import streamlit as st
import asyncio
from supabase import acreate_client, Client, AsyncClient
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def init_supabase() -> AsyncClient:
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Missing Supabase credentials")
        st.stop()
    return asyncio.run(acreate_client(url, key))

supabase: AsyncClient = init_supabase()

def get_current_user() -> Client.User | None:
    # Use sync client for quick auth check (or wrap async)
    sync_supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    try:
        session = sync_supabase.auth.get_session()
        return session.user if session and session.user else None
    except:
        return None
