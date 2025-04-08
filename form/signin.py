import streamlit as st
import toml
import os
# Check if running on Streamlit Cloud
if os.path.exists("./.streamlit/secrets.toml"):  # ✅ Running locally
    with open("./.streamlit/secrets.toml", "r") as f:
        secrets = toml.load(f)
    correct_username = secrets["credentials"]["USERNAME"]
    correct_password = secrets["credentials"]["PASSWORD"]
else:  # ✅ Running on Streamlit Cloud
    correct_username = st.secrets["credentials"]["USERNAME"]
    correct_password = st.secrets["credentials"]["PASSWORD"]

def sign_in():
    st.title("Sign In Page")
    with st.form(key="login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Sign In")
    if submit_button:
        if username == correct_username and password == correct_password:
            st.success(f"Welcome, {username}!")
            st.session_state.logged_in = True
            st.rerun()  # Force the page to rerun immediately
        elif username == correct_username:
            st.error("Incorrect password. Please try again.")
        else:
            st.error("Incorrect username. Please try again.")