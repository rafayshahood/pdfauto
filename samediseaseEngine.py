import streamlit as st
import openai
import time
import logging
import os
from dotenv import load_dotenv
import frontend.data.shared_data as shared_data
# Configure logging.
logging.basicConfig(level=logging.INFO)

# Load environment variables.
load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")

# -----------------------------------------------------
# For demonstration purposes, define extractionResults.
# extractionResults = shared_data.data['extraction_results']

def process_diseases():
    # Build the disease string and split it into an array.
    diseaseLength = 9
    
    patientDiseases = (
        shared_data.data['extraction_results']['patientDetails']['principalDiagnosis'] + "--" +
        shared_data.data['extraction_results']['patientDetails']['pertinentdiagnosis'] + "--" +
        shared_data.data['extraction_results']['diagnosis']['pertinentdiagnosisCont']
    )
    patientDiseasesArray = patientDiseases.split("--")

    # -----------------------------------------------------


    # Build initial disease messages.
    diseasesArray = []
    for i in range(diseaseLength):
        if i < len(patientDiseasesArray):
            diseasesArray.append(patientDiseasesArray[i])
        else:
            diseasesArray.append("")

    # -----------------------------------------------------
    # Initialize session state variables.
    if 'mainContResponse' not in st.session_state:
        st.session_state.mainContResponse = {}
    if 'used_index' not in st.session_state:
        st.session_state.used_index = diseaseLength 
    if 'diseasesArray' not in st.session_state:
        st.session_state.diseasesArray = diseasesArray
    if 'patientDiseasesArray' not in st.session_state:
        st.session_state.patientDiseasesArray = patientDiseasesArray
    if 'analysis_ran' not in st.session_state:
        st.session_state.analysis_ran = False

    # -----------------------------------------------------
    # Function to send a message and wait for its completion.
    def wait_for_run_completion(message, sleep_interval=5):
        client = openai.OpenAI()
        empty_thread = client.beta.threads.create()
        asistant_id = "asst_ugMOPS8hWwcUBYlT95sfJPXb"
        thread_id = empty_thread.id

        client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=message
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=asistant_id
        )
        while True:
            try:
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                if run.completed_at:
                    elapsed_time = run.completed_at - run.created_at
                    logging.info(f"Run completed in {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    last_message = messages.data[0]
                    response = last_message.content[0].text.value
                    client.beta.threads.delete(thread_id)
                    return response
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                client.beta.threads.delete(thread_id)
                break
            time.sleep(sleep_interval)

    # Function to check if a response is an error.
    def is_error_response(response):
        error_keywords = ["no disease found", "no medication found"]
        return any(keyword in response.lower() for keyword in error_keywords)

    # -----------------------------------------------------
    st.title("Disease Analysis App")

    # Callback to run the initial analysis.
    def run_initial_analysis():
        st.session_state.mainContResponse = {}
        for i in range(len(st.session_state.diseasesArray)): 
            message = st.session_state.diseasesArray[i]
            response = wait_for_run_completion(message)
            st.session_state.mainContResponse[f"page{i+1}"] = response
        st.session_state.analysis_ran = True
        st.rerun()  # Force a rerun to update the display immediately.

    # Run the initial analysis if not yet run.
    if not st.session_state.analysis_ran:
        if st.button("Generate Main Content"):
            run_initial_analysis()

    # If analysis has been run, display the responses.
    if st.session_state.analysis_ran:
        st.success("Initial Analysis Completed!")
        st.header("Responses")
        for page, response in st.session_state.mainContResponse.items():
            st.write(f"**{page}:** {response}")

        # Identify any invalid pages.
        invalid_pages = []
        for page, response in st.session_state.mainContResponse.items():
            if is_error_response(response):
                invalid_pages.append(page)

        invalid_pages = [page for page, response in st.session_state.mainContResponse.items() if is_error_response(response)]

        if invalid_pages:
            st.error("The following pages returned errors:")
            for page in invalid_pages:
                page_index = int(page.replace("page", "")) - 1
                try:
                    original_message = st.session_state.diseasesArray[page_index]
                    disease_name = original_message.split("disease name: ")[1].split(".")[0].strip()
                except Exception:
                    disease_name = "Unknown"
                st.write(f"**{page}:** {st.session_state.mainContResponse[page]}")
                st.write(f"Error: Disease/medication not found for '{disease_name}'.")
            
            if st.button("Re-run All Invalid Pages"):
                for page in invalid_pages:
                    page_index = int(page.replace("page", "")) - 1
                    if st.session_state.used_index < len(st.session_state.patientDiseasesArray):
                        new_message = (st.session_state.patientDiseasesArray[st.session_state.used_index])
                        st.write("DEBUG: New message for", page, ":", new_message)  # Debug line
                        st.session_state.used_index += 1
                        new_response = wait_for_run_completion(new_message)
                        st.write("DEBUG: New response for", page, ":", new_response)  # Debug line
                        st.session_state.mainContResponse[page] = new_response
                    else:
                        st.write(f"No more diseases available to replace for {page}.")
                st.success("Re-run for invalid pages completed!")
                shared_data.mainContResponse = st.session_state.mainContResponse
                st.rerun()
        else:
            # If no invalid pages remain, automatically redirect to the document filling page.
            shared_data.mainContResponse = st.session_state.mainContResponse
            st.success("All pages are valid. Redirecting to document filling page...")
            st.session_state["page"] = "doc"
            st.rerun()  # Force the app to rerun so that app.py detects the new page state.

# If this module is run directly, call process_diseases().
if __name__ == "__main__":
    process_diseases()