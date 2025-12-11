# --- Show Todos (Final Layout Fix Implemented) ---
# ...
if not todos:
    st.info("No todos yet — add one above!")
else:
    for todo in todos:
        completed = todo.get("is_complete", False)
        
        # Use st.container() to wrap the entire todo item
        with st.container(border=True): # border=True gives a native border that we will override
            # Apply custom CSS classes to the container content via a raw HTML marker
            # This is the trick to apply custom styles only to THIS container's contents
            st.markdown(f'<div class="todo-card-wrapper {"completed" if completed else ""}">', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([5, 1.5, 1.5]) 
            
            with c1:
                # Use st.markdown/st.write to output the text
                task_html = f'<span class="task-text">{todo["task"]}</span>'
                st.markdown(task_html, unsafe_allow_html=True) 
                
            # ... (buttons c2, c3 logic remains the same) ...
            
            with c2:
                # ... (buttons c2 logic remains the same) ...
                pass # (Button logic is below for brevity)
            
            with c3:
                # ... (buttons c3 logic remains the same) ...
                pass # (Button logic is below for brevity)

            st.markdown('</div>', unsafe_allow_html=True)

