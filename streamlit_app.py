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
        return [] # Return empty list if None is returned
        
    return data
        
except Exception as e:
    # A defensive return
    st.error(f"Failed to load todos: {str(e)}")  # Simplified error message for better UX
    return []