import streamlit as st
import json
import openai
import time
import logging
from dotenv import load_dotenv
import os
from fuzzywuzzy import process

# Load environment variables
load_dotenv()

# OpenAI API client
client = openai.OpenAI()

# OpenAI Assistant ID
assistant_id = "asst_ugMOPS8hWwcUBYlT95sfJPXb"

import json
import logging
import openai

def fetch_info_from_gpt(query_type, query_value, o2_flag=False, diabetec_flag=False):
    """
    Fetches disease or medication information using GPT-4o.
    
    Parameters:
        query_type (str): "disease" or "medication"
        query_value (str): The disease name or medication name to search for.
        o2_flag (bool): If True, adds the O₂-related sentence to text2.
        diabetec_flag (bool): If True, adds the diabetes-related sentence to text2.
    
    Returns:
        dict: JSON response containing the formatted output.
    """

    if query_type == "disease":
        gpt_prompt = f"""
        You are a **highly structured medical assistant** with access to **internet-based research and medical knowledge**.

        **TASK:** Search the internet or use your existing knowledge to retrieve structured medical information for the disease: '{query_value}'.

        **Response Format (STRICTLY FOLLOW THIS JSON FORMAT):**
        ```json
        {{
          "text1": "Altered status due to {query_value}. Knowledge deficit regarding measures to control {query_value} and the medication [insert medication] as ordered by MD.",
          "text2": "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. {add_special_conditions(o2_flag, diabetec_flag)}SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication [insert medication] as ordered by MD."
        }}
        ```
        📌 **GUIDELINES:**
        - STRICTLY return a **valid JSON response ONLY** (No additional text, explanations, or formatting outside the JSON block).
        - If the disease is **not found**, return:
          ```json
          {{
            "text1": "no disease found in database",
            "text2": "no disease found in database"
          }}
          ```
        """

    elif query_type == "medication":
        gpt_prompt = f"""
        You are a **highly structured medical assistant** with access to **internet-based research and medical knowledge**.

        **TASK:** Search the internet or use your existing knowledge to retrieve a recommended medication for the disease: '{query_value}'.

        **Response Format (STRICTLY FOLLOW THIS JSON FORMAT):**
        ```json
        {{
          "text1": "Altered status due to {query_value}. Knowledge deficit regarding measures to control {query_value} and the medication [insert medication] as ordered by MD.",
          "text2": "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. {add_special_conditions(o2_flag, diabetec_flag)}SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication [insert medication] as ordered by MD."
        }}
        ```
        📌 **GUIDELINES:**
        - STRICTLY return a **valid JSON response ONLY** (No additional text, explanations, or formatting outside the JSON block).
        - If no medication is **found**, return:
          ```json
          {{
            "text1": "no medication found in database",
            "text2": "no medication found in database"
          }}
          ```
        """

    else:
        return None  # Invalid query type

    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": gpt_prompt}]
        )

        gpt_result = gpt_response.choices[0].message.content.strip()

        # Log GPT raw response for debugging
        logging.info(f"GPT Raw Response for {query_type} '{query_value}':\n{gpt_result}")

        # Ensure JSON response is properly extracted
        json_start = gpt_result.find("{")
        json_end = gpt_result.rfind("}")

        if json_start == -1 or json_end == -1:
            logging.error(f"GPT response did not contain valid JSON: {gpt_result}")
            return return_no_data_response(query_type)  # Return appropriate fallback response

        json_response = gpt_result[json_start:json_end+1]  # Extract the JSON part only

        # Attempt to parse the extracted JSON
        parsed_response = json.loads(json_response)

        # Ensure correct structure
        if "text1" not in parsed_response or "text2" not in parsed_response:
            logging.error(f"GPT response is missing required fields: {parsed_response}")
            return return_no_data_response(query_type)

        return parsed_response

    except json.JSONDecodeError:
        logging.error(f"❌ JSONDecodeError: Failed to parse GPT response for {query_type}: {query_value}")
        print(f"❌ GPT response was not in correct JSON format:\n{gpt_result}")
        return return_no_data_response(query_type)  # Return fallback response

    except Exception as e:
        logging.error(f"❌ GPT API Error: {e}")
        return return_no_data_response(query_type)  # Handle general errors gracefully


def add_special_conditions(o2_flag, diabetec_flag):
    """
    Returns the additional condition-specific text if applicable.
    """
    condition_text = ""
    
    if o2_flag:
        condition_text += "Check O₂ saturation level with signs and symptoms of respiratory distress. "
    
    if diabetec_flag:
        condition_text += "SN to record blood sugar test results checked by Pt/PCG during the visits and report any significant changes to MD. SN to perform diabetic foot exam upon every visit. PCG assumes DM responsibilities, is confident, capable, and competent in checking blood sugar daily. "
    
    return condition_text


def return_no_data_response(query_type):
    """
    Returns a structured 'no data found' response based on query type.
    """
    if query_type == "disease":
        return {
            "text1": "no disease found in database",
            "text2": "no disease found in database"
        }
    elif query_type == "medication":
        return {
            "text1": "no medication found in database",
            "text2": "no medication found in database"
        }
    return None

# Sample extractedResults data
extractedResults = {
    "patientDetails": {
        "medicalRecordNo": "000000022-001",
        "name": "Pork, John",
        "providerName": "Mint Home Health Care Inc.",
        "principalDiagnosis": "diabetes mellitus with",
        "pertinentdiagnosis": "None -- None: -- Chronic kidney disease, unspec: -- Athscl heart disease of native -- Other disorders of lung -- Paroxysmal atrial fibrillation"
    },
    "diagnosis": {
        "pertinentdiagnosisCont": "Hypothyroidism, unspecified -- Mixed hyperlipidemia -- Old myocardial infarction -- Hypokalemia -- Gastro-esophageal reflux disease without esophagitis -- Hypomagnesemia -- Age-related cognitive decline -- Primary generalized (osteo) arthritis -- Vitamin D deficiency, unspecified -- Idiopathic gout, multiple sites -- Age-related osteoporosis w/o current pathological fracture -- Weakness -- Long term (current) use of anticoagulants -- Dependence on supplemental oxygen"
    },
    "medications": {
        "medications": "Ozempic 2 mg/3 ml, inject 0.5 mg subcutaneously daily; Janumet 50-500 mg, 1 tablet by mouth 2 times daily; Atorvastatin 20 mg, 1 tablet by mouth daily; Aspirin EC 81 mg, 1 tablet by mouth daily; Levothyroxine 75 mcg, 1 tablet by mouth daily; Allopurinol 100 mg, 1 tablet by mouth daily; Alendronate 70 mg, 1 tablet by mouth weekly; Omeprazole 40 mg, 1 tablet by mouth daily; Eliquis 2.5 mg, 1 tablet by mouth 2 times daily"
    }
}

# Extract diseases
patientDiseases = extractedResults['patientDetails']['principalDiagnosis'] + "--" + extractedResults['patientDetails']['pertinentdiagnosis'] + "--" + extractedResults['diagnosis']['pertinentdiagnosisCont']
patientDiseasesArray = patientDiseases.split("--")

diseasesArray = patientDiseasesArray[:3]  # Selecting first 6 diseases

# Extract medication list
provided_medications = set(
    med.strip().split(",")[0].lower()  # Extract medication name (before dosage)
    for med in extractedResults["medications"]["medications"].split(";")  # Splitting by semicolon
)

# Function to check if a disease is related to O₂ or diabetes
o2_related_keywords = ["copd", "respiratory failure", "pneumonia", "asthma", "hypoxia", "lung disease"]
diabetec_related_keywords = ["diabetes type 2", "dmii", "dm ii", "diabetic", "diabetes mellitus"]

def check_conditions(disease_name):
    disease_lower = disease_name.lower()
    o2_flag = any(keyword in disease_lower for keyword in o2_related_keywords)
    diabetec_flag = any(keyword in disease_lower for keyword in diabetec_related_keywords)
    return o2_flag, diabetec_flag

# Function that sends the request and waits for completion
def wait_for_run_completion(disease_name, o2=False, diabetec=False, sleep_interval=5):
    try:
        # Create a new thread for each request
        empty_thread = client.beta.threads.create()
        thread_id = empty_thread.id

        # Prepare the message with flags and medication list
        message_with_flags = f"Disease Name: {disease_name}\nO2Flag: {o2}\nDiabetesFlag: {diabetec}\nMedicationList: {list(provided_medications)}"

        # Send the request to the assistant
        client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=message_with_flags
        )

        # Start the assistant run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        # Wait for completion
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.completed_at:
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value

                # Delete the thread after retrieving the response
                client.beta.threads.delete(thread_id)
                return response

            logging.info("Waiting for run to complete...")
            time.sleep(sleep_interval)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None


# Initialize session state
if "mainContResponse" not in st.session_state:
    st.session_state["mainContResponse"] = {}

st.title("Medical Disease & Medication Processing")
st.subheader("Extracted Patient Information")
st.write(f"**Patient Name:** {extractedResults['patientDetails']['name']}")
st.write(f"**Medical Record No:** {extractedResults['patientDetails']['medicalRecordNo']}")
st.write(f"**Provider:** {extractedResults['patientDetails']['providerName']}")

# Button to run the assistant processing
if st.button("Run Disease Processing"):
    st.write("⏳ Processing diseases...")
    progress_bar = st.progress(0)

    for i, disease_name in enumerate(diseasesArray):
        o2_flag, diabetec_flag = check_conditions(disease_name)
        response = wait_for_run_completion(disease_name, o2=o2_flag, diabetec=diabetec_flag)
        st.session_state["mainContResponse"][f"page{i + 1}"] = response
        progress_bar.progress((i + 1) / len(diseasesArray))

    st.success("✅ Processing Completed!")



invalid_pages = []
missing_medication_pages = []

# Identify pages that need modification
for page, response_json in st.session_state["mainContResponse"].items():
    if page in st.session_state["skipped_pages"]:
        continue  # Ignore already skipped pages

    response = json.loads(response_json)
    if response["text1"] == "no disease found in database":
        invalid_pages.append(page)
    elif response["text1"] == "no medication found in database":
        missing_medication_pages.append(page)

# --- Track invalid pages ---
if "skipped_pages" not in st.session_state:
    st.session_state["skipped_pages"] = set()

# --- Track invalid pages ---
if "replacement_start_index" not in st.session_state:
    st.session_state["replacement_start_index"] = len(diseasesArray)

# # --- Track invalid pages ---
if "used_disease_indices" not in st.session_state:
    st.session_state["used_disease_indices"] = set()

# --- Identify missing diseases & medications ---
if invalid_pages or missing_medication_pages:
    st.warning("⚠️ Some diseases or medications were not found. Please modify below.")

    for page in invalid_pages:
        st.subheader(f"🔴 Disease Not Found on {page}")
        disease_index = int(page.replace("page", "")) - 1
        original_disease = diseasesArray[disease_index].strip()

        # --- Find a new replacement disease ---
        next_valid_disease = None
        for j in range(st.session_state["replacement_start_index"], len(patientDiseasesArray)):
            if j not in st.session_state["used_disease_indices"]:
                candidate_disease = patientDiseasesArray[j].strip()
                if candidate_disease and candidate_disease.lower() != "none":
                    next_valid_disease = candidate_disease
                    st.session_state["used_disease_indices"].add(j)
                    st.session_state["replacement_start_index"] = j + 1  # Ensure next disease is different
                    break

        # Store the replacement disease in session state
        if f"replacement_disease_{page}" not in st.session_state:
            st.session_state[f"replacement_disease_{page}"] = next_valid_disease if next_valid_disease else original_disease

        # --- Input box for new replacement disease ---
        retry_disease = st.text_input(
            f"Enter new disease for {page}", 
            st.session_state[f"replacement_disease_{page}"], 
            key=f"retry_disease_{page}"
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button(f"✔️ Retry with {retry_disease}", key=f"retry_btn_{page}"):
                with st.spinner(f"Updating {retry_disease}..."):
                    o2_flag, diabetec_flag = check_conditions(retry_disease)
                    response = wait_for_run_completion(retry_disease, o2=o2_flag, diabetec=diabetec_flag)
                    # Ensure response is correctly parsed as JSON
                    try:
                        parsed_response = json.loads(response) if isinstance(response, str) else response
                        st.session_state["mainContResponse"][page] = json.dumps(parsed_response)
                    except json.JSONDecodeError:
                        st.error("Error processing the response. Please try again.")
                st.rerun()

        with col2:
            if st.button(f"🌐 Ask GPT for {original_disease}", key=f"gpt_{page}"):
                with st.spinner(f"Fetching data for {original_disease}..."):
                    gpt_result = fetch_info_from_gpt("disease", original_disease)
                    # Ensure GPT response is correctly parsed as JSON
                    if gpt_result:
                        try:
                            parsed_response = json.loads(gpt_result) if isinstance(gpt_result, str) else gpt_result
                            st.session_state["mainContResponse"][page] = json.dumps(parsed_response)
                        except json.JSONDecodeError:
                            st.error("Error processing GPT response. Please try again.")

                st.rerun()

        with col3:
            if st.button(f"🌐 Ask GPT for {retry_disease}", key=f"gpt_med_{page}"):
                with st.spinner(f"Fetching medication for {retry_disease}..."):
                    # Ensure GPT response is correctly parsed as JSON
                    gpt_result = fetch_info_from_gpt("disease", retry_disease)
                    if gpt_result:
                        try:
                            parsed_response = json.loads(gpt_result) if isinstance(gpt_result, str) else gpt_result
                            st.session_state["mainContResponse"][page] = json.dumps(parsed_response)
                        except json.JSONDecodeError:
                            st.error("Error processing GPT response. Please try again.")
                st.rerun()

        with col4:
            if st.button(f"❌ Skip {page}", key=f"skip_{page}"):
                with st.spinner(f"Skipping {original_disease}..."):
                    st.session_state["skipped_pages"].add(page)
                    st.session_state["mainContResponse"][page] = json.dumps({
                        "text1": "no disease found in database",
                        "text2": "no disease found in database"
                    })
                st.rerun()


    for page in missing_medication_pages:
        st.subheader(f"🟠 Medication Not Found on {page}")
        disease_index = int(page.replace("page", "")) - 1
        disease_name = diseasesArray[disease_index]

        retry_med = st.text_input(f"Enter new medication for {page}", "", key=f"retry_med_{page}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"✔️ Retry with {retry_med}", key=f"retry_med_btn_{page}"):
                with st.spinner(f"Updating medication..."):
                    st.session_state["mainContResponse"][page] = json.dumps({"text1": retry_med, "text2": retry_med})
                st.rerun()

        with col2:
            if st.button(f"🌐 Ask GPT for {disease_name}", key=f"gpt_med_{page}"):
                with st.spinner(f"Fetching medication for {disease_name}..."):
                    gpt_result = fetch_info_from_gpt("medication", disease_name)
                    if gpt_result:
                        st.session_state["mainContResponse"][page] = json.dumps(gpt_result)
                st.rerun()

        with col3:
            if st.button(f"❌ Skip {page}", key=f"skip_med_{page}"):
                with st.spinner(f"Skipping medication for {disease_name}..."):
                    st.session_state["skipped_pages"].add(page)  # Store skipped page
                    st.session_state["mainContResponse"][page] = json.dumps({
                        "text1": "no medication found in database",
                        "text2": "no medication found in database"
                    })
                st.rerun()

# --- Final Display: Show Processed Results If No Issues Exist ---
if not invalid_pages and not missing_medication_pages and st.session_state["mainContResponse"] != {}:
    st.success("✅ All diseases and medications were processed successfully!")

    st.subheader("📄 Processed Responses")
    for page, response_json in st.session_state["mainContResponse"].items():
        response = json.loads(response_json)
        st.markdown(f"### 📝 {page}")
        st.write(f"**Text1:** {response['text1']}")
        st.write(f"**Text2:** {response['text2']}")