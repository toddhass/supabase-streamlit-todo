# ─── Logout & User Info ─────────────────────
if st.session_state.user:
    cols = st.columns([3, 1])
    with cols[1]:
        if st.button("Log out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.auth_checked = False
            st.success("Logged out successfully")
            st.rerun()
    
    # ← CORRECTED LINE (was missing closing brace)
    st.caption(f"Logged in as: **{st.session_state.user.email}**")