import hashlib
import hmac
import streamlit as st
import os

# Ideally, store this in an environment variable
# For now, we'll hardcode a default for the project
ADMIN_PASSWORD_HASH = hashlib.sha256("hunter2".encode()).hexdigest()

def check_password(password: str) -> bool:
    """
    Verifies the provided password against the stored hash.
    """
    # Hash the input password
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Secure comparison to prevent timing attacks
    return hmac.compare_digest(input_hash, ADMIN_PASSWORD_HASH)

def login_form():
    """
    Renders the login form and handles state.
    """
    st.markdown("""
        <style>
            .stTextInput > div > div > input {
                background-color: #0e1117;
                color: #00ff41;
                border: 1px solid #00ff41;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🛡️ Restricted Access")
    
    password = st.text_input("Enter Access Code", type="password")
    
    if st.button("Authenticate"):
        if check_password(password):
            st.session_state["authenticated"] = True
            st.success("Access Granted.")
            st.rerun()
        else:
            st.error("⛔ Access Denied.")