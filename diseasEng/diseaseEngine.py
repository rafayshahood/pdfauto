import streamlit as st
import json
import openai
from dotenv import load_dotenv
import data.shared_data as shared_data
from diseasEng.helperFunctions import fetch_info_from_gpt, wait_for_run_completion, fetch_info_from_gpt2, find_closest_medication
import time
from fuzzywuzzy import process  # Import fuzzy string matching

# Load environment variables
load_dotenv()
# OpenAI API client
client = openai.OpenAI()
# OpenAI Assistant ID
assistant_id = "asst_ugMOPS8hWwcUBYlT95sfJPXb"


def process_diseases():
    
    # gpt2_used_pages = []  # ✅ Track pages where we used GPT2 due to empty medication list
    extractedResults = shared_data.data['extraction_results']

    # Extract diseases
    patientDiseases = extractedResults['patientDetails']['principalDiagnosis'] + "--" + extractedResults['patientDetails']['pertinentdiagnosis'] + "--" + extractedResults['diagnosis']['pertinentdiagnosisCont']
    patientDiseasesArray = patientDiseases.split("--")

    # print(f"patient disease array:  {patientDiseasesArray}")
    diseasesArray = patientDiseasesArray[:9]  # Selecting first 10 diseases

    # Extract medication list
    provided_medications = set(
        med.strip().split(" by ")[0].lower()  # Extract medication name (before administration details)
        for med in extractedResults["medications"]["medications"].split("--")  # Splitting by comma
    )
    
    # print(f"provided_medications: {provided_medications}" )


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
            if provided_medications:  # ✅ Use OpenAI Assistant if medications exist
                response = wait_for_run_completion(client, assistant_id, disease_name, provided_medications, o2=oxygen_flag, diabetec=diabetec_flag)
                # print(f" wait for run: {response}")
            else:  # ✅ Use GPT if no medications exist
                response = fetch_info_from_gpt2(client, disease_name)
                shared_data.gpt2_used_pages.append(i + 1)  # ✅ Store page number
                # print(f" gpt2: {response}")

            # response = wait_for_run_completion(client, assistant_id, disease_name, provided_medications, o2=oxygen_flag, diabetec=diabetec_flag)
            response_json = json.loads(response) if isinstance(response, str) else response
            st.session_state["mainContResponse"][f"page{i + 1}"] = json.dumps(response_json)

            # ✅ Store disease used for each page
            st.session_state["disease_mapping"][f"page{i + 1}"] = disease_name

            # **Remove the medication that was used** (if a valid medication was assigned)
            if "med" in response_json and response_json["med"] not in ["no medication found in database", ""]:
                used_medication = response_json["med"]
                
                # Find the closest match in provided_medications_list
                closest_match = find_closest_medication(used_medication, provided_medications)
                
                if closest_match:
                    provided_medications.remove(closest_match)  # Remove the closest matching medication
            
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
                st.session_state[f"replacement_disease_{page}"] = next_valid_disease

            # Ensure retry_disease is always initialized
            retry_disease = st.session_state.get(f"replacement_disease_{page}", "").strip()

            # --- Input box for new replacement disease ---
            retry_disease = st.text_input(
                f"Enter new disease for {page}", 
                retry_disease, 
                key=f"retry_disease_{page}"
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(f"✔️ Retry with {retry_disease}", key=f"retry_btn_{page}"):
                    with st.spinner(f"Updating {retry_disease}..."):
                        response = wait_for_run_completion(client, assistant_id, retry_disease, provided_medications, o2=oxygen_flag, diabetec=diabetec_flag)
                        print(f"API Response for {retry_disease}: {response}")  # Debugging
                        try:
                            parsed_response = json.loads(response) if isinstance(response, str) else response
                            st.session_state["mainContResponse"][page] = json.dumps(parsed_response)

                            # ✅ Update disease mapping for retried disease
                            st.session_state["disease_mapping"][page] = retry_disease

                            # **Remove the medication that was used (if applicable)**
                            if "med" in parsed_response and parsed_response["med"] not in ["no medication found in database", ""]:
                                used_medication = parsed_response["med"]
                                
                                # Find the closest match in provided_medications_list
                                closest_match = find_closest_medication(used_medication, provided_medications)
                                
                                if closest_match:
                                    provided_medications.remove(closest_match)  # Remove the closest matching medication
                        
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

                                # ✅ Update disease mapping for retried disease
                                st.session_state["disease_mapping"][page] = retry_disease
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

            col1, col2, col3, col4 = st.columns(4)
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

            # Ensure retry_disease is always initialized
            retry_disease = st.session_state.get(f"replacement_disease_{page}", "").strip()

            # Provide input field for user modification
            retry_disease = st.text_input(
                f"Enter new disease for {page}", 
                retry_disease, 
                key=f"retry_disease_{page}")

            with col1:
                    if st.button(f"✔️ Retry with {retry_disease}", key=f"retry_btn_{page}"):
                        with st.spinner(f"Updating {retry_disease}..."):
                            response = wait_for_run_completion(client, assistant_id, retry_disease, provided_medications, o2=oxygen_flag, diabetec=diabetec_flag)
                            try:
                                parsed_response = json.loads(response) if isinstance(response, str) else response
                                st.session_state["mainContResponse"][page] = json.dumps(parsed_response)

                                st.session_state["disease_mapping"][page] = retry_disease

                                # **Remove the medication that was used (if applicable)**
                                if "med" in parsed_response and parsed_response["med"] not in ["no medication found in database", ""]:
                                    used_medication = parsed_response["med"]
                                    
                                    # Find the closest match in provided_medications_list
                                    closest_match = find_closest_medication(used_medication, provided_medications)
                                    
                                    if closest_match:
                                        provided_medications.remove(closest_match)  # Remove the closest matching medication
                            
                            except json.JSONDecodeError:
                                st.error("Error processing the response. Please try again.")
                        st.rerun()


            with col2:
                # ✅ Option 2: Fetch a new medication from GPT
                if st.button(f"🌐 Ask GPT for a new medication", key=f"gpt_med_new_{page}"):
                    with st.spinner(f"Fetching new medication for {disease_name}..."):
                        gpt_result = fetch_info_from_gpt(client, "disease", disease_name)
                        if gpt_result:
                            try:
                                parsed_response = json.loads(gpt_result) if isinstance(gpt_result, str) else gpt_result
                                st.session_state["mainContResponse"][page] = json.dumps(parsed_response)
                            except json.JSONDecodeError:
                                st.error("Error processing GPT response. Please try again.")
                    st.rerun()


            with col3:
            # ✅ Option 3: Get the output from GPT **without medication**
                if st.button(f"🌐 Get disease info without No medication", key=f"gpt_no_med_{page}"):
                    with st.spinner(f"Fetching disease information without medication..."):
                        gpt_result = fetch_info_from_gpt2(client, disease_name)
                        if gpt_result:
                            try:
                                parsed_response = json.loads(gpt_result) if isinstance(gpt_result, str) else gpt_result
                                parsed_response["med"] = "no medication found in database"  # Ensure medication is left empty
                                st.session_state["mainContResponse"][page] = json.dumps(parsed_response)
                                # shared_data.gpt2_used_pages.append(i + 1)  # ✅ Store page number

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