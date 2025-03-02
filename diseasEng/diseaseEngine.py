import streamlit as st
import json
import openai
from dotenv import load_dotenv
import data.shared_data as shared_data
from diseasEng.helperFunctions import fetch_info_from_gpt, wait_for_run_completion
import time

# Load environment variables
load_dotenv()
# OpenAI API client
client = openai.OpenAI()
# OpenAI Assistant ID
assistant_id = "asst_ugMOPS8hWwcUBYlT95sfJPXb"

# # Sample extractedResults data
# extractedResults = {
#     "patientDetails": {
#         "medicalRecordNo": "000000022-001",
#         "name": "Pork, John",
#         "providerName": "Mint Home Health Care Inc.",
#         "principalDiagnosis": "diabetes mellitus with",
#         "pertinentdiagnosis": "None -- None: -- Chronic kidney disease, unspec: -- Athscl heart disease of native -- Other disorders of lung -- Paroxysmal atrial fibrillation"
#     },
#     "diagnosis": {
#         "pertinentdiagnosisCont": "Hypothyroidism, unspecified -- Mixed hyperlipidemia -- Old myocardial infarction -- Hypokalemia -- Gastro-esophageal reflux disease without esophagitis -- Hypomagnesemia -- Age-related cognitive decline -- Primary generalized (osteo) arthritis -- Vitamin D deficiency, unspecified -- Idiopathic gout, multiple sites -- Age-related osteoporosis w/o current pathological fracture -- Weakness -- Long term (current) use of anticoagulants -- Dependence on supplemental oxygen"
#     },
#     "medications": {
#         "medications": "Ozempic 2 mg/3 ml, inject 0.5 mg subcutaneously daily; Janumet 50-500 mg, 1 tablet by mouth 2 times daily; Atorvastatin 20 mg, 1 tablet by mouth daily; Aspirin EC 81 mg, 1 tablet by mouth daily; Levothyroxine 75 mcg, 1 tablet by mouth daily; Allopurinol 100 mg, 1 tablet by mouth daily; Alendronate 70 mg, 1 tablet by mouth weekly; Omeprazole 40 mg, 1 tablet by mouth daily; Eliquis 2.5 mg, 1 tablet by mouth 2 times daily"
#     }
# }


def process_diseases():
    extractedResults = shared_data.data['extraction_results']

    # Extract diseases
    patientDiseases = extractedResults['patientDetails']['principalDiagnosis'] + "--" + extractedResults['patientDetails']['pertinentdiagnosis'] + "--" + extractedResults['diagnosis']['pertinentdiagnosisCont']
    patientDiseasesArray = patientDiseases.split("--")

    diseasesArray = patientDiseasesArray[:9]  # Selecting first 6 diseases

    # Extract medication list
    provided_medications = set(
        med.strip().split(",")[0].lower()  # Extract medication name (before dosage)
        for med in extractedResults["medications"]["medications"].split(";")  # Splitting by semicolon
    )

    diabetec_flag = extractedResults['diagnosis']['diabetec']
    oxygen_flag = extractedResults['diagnosis']['oxygen']


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
            response = wait_for_run_completion(client, assistant_id, disease_name, provided_medications, o2=oxygen_flag, diabetec=diabetec_flag)
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
                        response = wait_for_run_completion(client, assistant_id, retry_disease, provided_medications, o2=oxygen_flag, diabetec=diabetec_flag)
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
                        gpt_result = fetch_info_from_gpt(client, "disease", original_disease)
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
                    with st.spinner(f"Fetching data for {retry_disease}..."):
                        # Ensure GPT response is correctly parsed as JSON
                        gpt_result = fetch_info_from_gpt(client, "disease", retry_disease)
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

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(f"✔️ Retry with {retry_med}", key=f"retry_med_btn_{page}"):
                    with st.spinner(f"Updating medication..."):
                        st.session_state["mainContResponse"][page] = json.dumps({"text1": retry_med, "text2": retry_med})
                    st.rerun()

            with col2:
                if st.button(f"🌐 Ask GPT for {disease_name}", key=f"gpt_med_{page}"):
                    with st.spinner(f"Fetching medication for {disease_name}..."):
                        gpt_result = fetch_info_from_gpt(client, "medication", disease_name)
                        if gpt_result:
                            st.session_state["mainContResponse"][page] = json.dumps(gpt_result)
                    st.rerun()

            with col3:
                if st.button(f"🌐 Ask GPT for {retry_disease}", key=f"gpt_med_{page}"):
                    with st.spinner(f"Fetching data for {retry_disease}..."):
                        # Ensure GPT response is correctly parsed as JSON
                        gpt_result = fetch_info_from_gpt(client, "disease", retry_disease)
                        if gpt_result:
                            try:
                                parsed_response = json.loads(gpt_result) if isinstance(gpt_result, str) else gpt_result
                                st.session_state["mainContResponse"][page] = json.dumps(parsed_response)
                            except json.JSONDecodeError:
                                st.error("Error processing GPT response. Please try again.")
                    st.rerun()

            with col4:
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
        shared_data.mainContResponse = st.session_state["mainContResponse"]
        st.session_state["page"] = "doc"
        st.rerun()

        # st.subheader("📄 Processed Responses")
        # for page, response_json in st.session_state["mainContResponse"].items():
        #     response = json.loads(response_json)
        #     st.markdown(f"### 📝 {page}")
        #     st.write(f"**Text1:** {response['text1']}")
        #     st.write(f"**Text2:** {response['text2']}")