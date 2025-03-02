import openai
from dotenv import load_dotenv
import time
import logging
from datetime import datetime
import os
import frontend.data.shared_data as shared_data
import streamlit as st  # For UI elements
import json

load_dotenv()


def wait_for_run_completion(message, client, thread_id, run_id, sleep_interval=5):
    """
    Waits for a run to complete and returns the response.
    """
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
                logging.info(f"Run completed in {formatted_elapsed_time}")
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                return response
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            break
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)
        
def process_diseases():
    extractionResults = shared_data.data.get("extraction_results", {})
    # Define expected_count before using it later in the function.
    expected_count = 2  

    if shared_data.mainContResponse == {}:
        # Concatenate diagnosis fields.
        patientDiseases = (
            extractionResults['patientDetails']['principalDiagnosis']
            + "--" + extractionResults['patientDetails']['pertinentdiagnosis']
            + "--" + extractionResults['diagnosis']['pertinentdiagnosisCont']
        )
        patientDiseasesArray = patientDiseases.split("--")

        if len(patientDiseasesArray) < expected_count:
            st.warning(f"Expected {expected_count} diseases but got {len(patientDiseasesArray)}. Padding with empty strings.")
            patientDiseasesArray.extend([""] * (expected_count - len(patientDiseasesArray)))

        # Define a common output format.
        outputFormat1 = (
            "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. "
            "SN to assess vital signs, pain level. SN to record blood sugar test results checked by Pt/PCG during the visits and report any significant changes to MD. "
            "SN to perform diabetic foot exam upon every visit. SN/Caregiver to administer Ozempic injections. "
            "PCG assumes DM responsibilities, is confident, capable and competent in checking blood sugar daily and diabetic foot exam/care via return demonstration. "
            "SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues, and psychosocial adjustment. "
            "SN instructed patient/PCG regarding signs and symptoms of Type 2 diabetes mellitus. Diabetes mellitus is more commonly known simply as diabetes. "
            "It's when your pancreas doesn't produce enough insulin to control the amount of glucose, or sugar, in your blood. The symptoms are: excessive thirst, "
            "excessive intake of fluids, fatigue, increased urination, dry hot skin, itching, and weakness."
        )
        diseaseOutputFormats = [outputFormat1] * expected_count

        # Build disease strings.
        disease_strings = []
        for i in range(expected_count):
            disease_str = "disease name: " + patientDiseasesArray[i] + " Output format: " + diseaseOutputFormats[i]
            disease_strings.append(disease_str)
        diseasesArray = disease_strings

        mainContResponse = {f"{i+1}": None for i in range(expected_count)}

        # Setup the assistant.
        client = openai.OpenAI()
        empty_thread = client.beta.threads.create()
        assistant_id = "asst_ugMOPS8hWwcUBYlT95sfJPXb"
        thread_id = empty_thread.id

        # For each page, if no response exists, run the assistant.
        for i in range(expected_count):
            page_key = f"{i+1}"
            if mainContResponse.get(page_key) in [None, page_key]:
                client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=diseasesArray[i]
                )
                run = client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                )
                mainContResponse[page_key] = wait_for_run_completion(
                    diseasesArray[i], client=client, thread_id=thread_id, run_id=run.id
                )
        shared_data.mainContResponse = mainContResponse
        shared_data.patientDiseasesArray = patientDiseasesArray
        shared_data.diseaseOutputFormats = diseaseOutputFormats

        st.write("### Current Assistant Responses")
        st.write(shared_data.mainContResponse)
    mainContResponse = shared_data.mainContResponse
    patientDiseasesArray = shared_data.patientDiseasesArray
    diseaseOutputFormats = shared_data.diseaseOutputFormats

    # Build a list of replacement tasks.
    replacements = shared_data.replacements 
    for page, response in mainContResponse.items():
        disease_index = int(page) - 1
        current_disease = patientDiseasesArray[disease_index]
        if response is None:
            replacements.append({"page": page, "invalid_disease": current_disease, "warnVal": "No response"})
        else:
            lower_response = response.lower()
            if "no disease found" in lower_response:
                replacements.append({"page": page, "invalid_disease": current_disease, "warnVal": "disease"})
            elif "no medication found" in lower_response:
                replacements.append({"page": page, "invalid_disease": current_disease, "warnVal": "medication"})

    # Display replacement suggestions.
    if len(replacements) > 0:
        st.subheader("Replacement Suggestions")
        for i, rep in enumerate(replacements):
            candidate_idx = expected_count + i  # Start replacements after the initial expected_count
            if candidate_idx < len(patientDiseasesArray):
                new_disease_name = patientDiseasesArray[candidate_idx]
                st.info(
                    f"Page {rep['page']}: '{rep['invalid_disease']}' did not return valid {rep['warnVal']} information. "
                    f"It will be replaced with '{new_disease_name}'."
                )
            else:
                st.error(f"No candidate replacement available for '{rep['invalid_disease']}' on Page {rep['page']}.")

        # Single button to process all replacements.
        if st.button("Make Replacements"):
            for i, rep in enumerate(replacements):
                candidate_idx = expected_count + i  # Use the proper ordering
                if candidate_idx < len(patientDiseasesArray):
                    new_disease_name = patientDiseasesArray[candidate_idx]
                    page_idx = int(rep["page"]) - 1
                    new_disease_str = (
                        "disease name: " + new_disease_name +
                        " Output format: " + diseaseOutputFormats[page_idx]
                    )
                    # Setup the assistant for replacement.
                    client = openai.OpenAI()
                    empty_thread = client.beta.threads.create()
                    assistant_id = "asst_ugMOPS8hWwcUBYlT95sfJPXb"
                    thread_id = empty_thread.id

                    client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=new_disease_str
                    )
                    run = client.beta.threads.runs.create(
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                    )
                    new_response = wait_for_run_completion(
                        new_disease_str, client=client, thread_id=thread_id, run_id=run.id
                    )
                    mainContResponse[rep["page"]] = new_response
                    shared_data.mainContResponse[rep["page"]] = mainContResponse

                else:
                    st.error(f"No candidate available for replacement on Page {rep['page']}.")
            st.write("### Updated Responses")
            st.write(mainContResponse)
            # Update shared data and refresh the page.
            replacements = []
            shared_data.replacements = replacements

        st.session_state["page"] = "results"
        st.rerun()
    else:
        st.write("### New Responses")
        st.write(shared_data.mainContResponse)
        st.session_state["page"] = "results"
        # st.rerun()
        # st.session_state["page"] = "output-doc"