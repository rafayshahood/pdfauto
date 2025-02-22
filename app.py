import streamlit as st
import tempfile
import sys
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from form import complete_form
import shared_data
from signin import sign_in
from samediseaseEngine import process_diseases
from wordFilling import fillDoc
def showResults():
    st.write("### Submission Details and Extraction Results")
    st.json(shared_data.data)


def main():
    # Set default page if not already set.
    if "page" not in st.session_state:
        st.session_state["page"] = "form"
    
    # Authentication
    if "logged_in" not in st.session_state:
        sign_in()
    elif st.session_state.logged_in:
        # Navigate based on page state.
        if st.session_state.page == "form":
            complete_form()
        elif st.session_state.page == "disease":
            process_diseases()  # This function contains your disease analysis engine.
        elif st.session_state.page == "doc":
            fillDoc()  # This function contains your disease analysis engine.    
        else:
            st.write("Unknown page state.")


if __name__ == "__main__":
    main()