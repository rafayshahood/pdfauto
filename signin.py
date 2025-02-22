import streamlit as st
import tempfile
import sys
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from form import complete_form
import shared_data
from diseaseEngine import process_diseases


correct_username = ""
correct_password = ""

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