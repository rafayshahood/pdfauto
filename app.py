import streamlit as st
# from frontend.form.form import complete_form
# from frontend.form.signin import sign_in
from form.signin import sign_in
from form.form import complete_form  # Ensure this import is correct
from filling.wordFilling import fillDoc  # Ensure this import is correct
from diseasEng.diseaseEngine import process_diseases
from filling.wordFilling import fillDoc

def main():

    # 🔄 **One-Time Session State Initialization**
    if "initialized" not in st.session_state:
        print("🔄 Resetting session state variables for a clean run...")

        st.session_state.clear()  # Clears all session state variables

        # Reinitialize necessary session state variables
        st.session_state["mainContResponse"] = {}
        st.session_state["skipped_pages"] = set()
        st.session_state["replacement_start_index"] = 0
        st.session_state["used_disease_indices"] = set()

        st.session_state["initialized"] = True  # Mark initialization as complete
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

        elif st.session_state.page == "doc":
            fillDoc()  # This function contains your disease analysis engine.    

        elif st.session_state.page == "disease_analysis":
            process_diseases()  # New function to process diseases and medications

        else:
            st.write("Unknown page state.")


if __name__ == "__main__":
    main()