# utils.py
import os
import streamlit as st
import nest_asyncio
from supabase import create_client, acreate_client, Client, AsyncClient
from dotenv import load_dotenv

# Patch for Streamlit's running loop
nest_asyncio.apply()

load_dotenv()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets.get("SUPABASE_URL"), st.secrets.get("SUPABASE_KEY"))

@st.cache_resource
def init_async_supabase() -> AsyncClient:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(acreate_client(st.secrets.get("SUPABASE_URL"), st.secrets.get("SUPABASE_KEY")))

supabase = init_supabase()
async_supabase = init_async_supabase()

def get_current_user():
    try:
        session = supabase.auth.get_session()
        return session.user if session and session.user else None
    except:
        return None
