# utils.py
import streamlit as st
import nest_asyncio
from supabase import create_client, acreate_client, Client
import asyncio

nest_asyncio.apply()  # Allows async in Streamlit

@st.cache_resource
def get_sync_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def get_async_client():
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(acreate_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]))

supabase = get_sync_client()
async_supabase = get_async_client()

def get_current_user():
    try:
        session = supabase.auth.get_session()
        return session.user if session and session.user else None
    except:
        return None
