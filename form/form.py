import streamlit as st
import tempfile
from datetime import datetime, timedelta
import data.shared_data as shared_data
from form.extraction import main as extractionMain

def get_ordinal(n: int) -> str:
    if n == 1:
        return "1st"
    elif n == 2:
        return "2nd"
    elif n == 3:
        return "3rd"
    else:
        return f"{n}th"

def complete_form():
    st.header("Appointment Details and PDF Upload")
    action = st.radio("Select Action", options=["Discharge", "Reset"], key="action")
    
    with st.form("complete_form"):
        sn_name = st.text_input("SN Name", key="sn_name")
        appointment_dates = []
        appointment_times = []
        st.write("Enter the appointment dates and times:")
        for i in range(1, 10):
            col1, col2 = st.columns(2)
            with col1:
                date_val = st.date_input(f"{get_ordinal(i)} Appointment Date", key=f"date_{i}")
            with col2:
                time_val = st.time_input(f"{get_ordinal(i)} Appointment Time", key=f"time_{i}")
            appointment_dates.append(date_val)
            appointment_times.append(time_val)
        
        if action == "Discharge":
            st.write("Enter additional appointment details for Reset (10th appointment):")
            col1, col2 = st.columns(2)
            with col1:
                reset_date = st.date_input("10th Appointment Date", key="reset_date")
            with col2:
                reset_time = st.time_input("10th Appointment Time", key="reset_time")
            appointment_dates.append(reset_date)
            appointment_times.append(reset_time)
        
        uploaded_file = st.file_uploader("Upload a PDF", type="pdf", key="pdf_file")
        submit_all = st.form_submit_button("Submit All Details")
    
    if submit_all:
        if not sn_name:
            st.error("Please fill in SN Name.")
            return
        if uploaded_file is None:
            st.error("Please upload a PDF document.")
            return

        # Store the dates in dd/mm/YYYY format (for user input)
        formatted_dates = [d.strftime("%d/%m/%Y") for d in appointment_dates]
        formatted_times = []
        for t in appointment_times:
            dt = datetime.combine(datetime.today(), t)
            end_dt = dt + timedelta(minutes=45)
            start_str = dt.strftime("%H:%M")
            end_str = end_dt.strftime("%H:%M")
            formatted_times.append(f"{start_str}-{end_str}")
            # formatted_times.append(f"{start_str}-{end_str}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name

        # extraction_result = extractionMain(tmp_file_path)

        extraction_result = {
            'patientDetails': 
                {'medicalRecordNo': '000000156-001', 
                    'name': 'FORD, HENRY', 
                    'providerName': 'MINT Home Health Care Inc.', 
                    'principalDiagnosis': 'Primary osteoarthritis, left shoulder', 
                    'pertinentdiagnosis': 'vsd, right -- Spondylosis w/o myelopathy or radiculopathy -- Essential (primary) hypertension -- Unspecified asthma, uncomplicated -- Edema, unspecified -- Weakness -- Iron deficiency anemia, unspecified -- Hyperlipidemia, unspecified -- Vitamin D deficiency, unspecified -- History of falling'}, 
                'diagnosis': 
                    {'pertinentdiagnosisCont': '', 
                     'constipated': False, 
                     'painIn': 'Lower Back, Bilateral Shoulders, Joints', 
                     'diabetec': False, 
                     'oxygen': False, 
                     'depression': False}, 
                'medications': 
                    {'medications': 'Chlorthalidone 25 mg, 1 tablet by mouth daily -- Rosuvastatin 10 mg, 1 tablet by mouth daily -- Magnesium 250 mg, 1 tablet by mouth daily -- Albuterol HFA 90 mcg, inhale 2 puffs by mouth 2 times daily -- Aspirin 81 mg, 1 tablet by mouth daily -- Ibuprofen 600 mg, 1 tablet by mouth every 6 hours as needed for pain -- Pain Reliever Ointment Gel, apply topically to affected area 2 times daily -- Ferrous Sulfate 325 mg, 1 tablet by mouth daily -- Vitamin D3 2000 International Units, 1 capsule by mouth daily -- Oyster Shell Calcium 500 mg, 1 tablet by mouth daily -- Tylenol 500 mg, 1 capsule by mouth every 6 hours as needed for pain', 
                     'painMedications': 'Ibuprofen 600 mg, 1 tablet by mouth every 6 hours as needed for pain'}, 
                'extraDetails': 
                    {'safetyMeasures': 'Bleeding precautions, Fall precautions, Clear pathways, Infection control -- Walker, Cane, Universal Precautions, 911 protocol, COVID-19 Precautions', 
                     'nutritionalReq': 'NAS, Low fat, Low cholesterol', 
                     'nutritionalReqCont': '', 
                     'edema': 'Pedal R/L, Pitting +1',
                       'vertigo': False, 
                       'palpitation': False,
                       'can': 'true', 
                       'walker': 'true'}}
        # extraction_result = {
        #                     "patientDetails": {
        #                         "medicalRecordNo": "000000022-001",
        #                         "name": "Pork, Johnvi",
        #                         "providerName": "Mint Home Health Care Inc.",
        #                         "principalDiagnosis": "diabetes mellitus with",
        #                         "pertinentdiagnosis": "Acute diastolic (congestive) heart failure -- Hyp hrt & chr kdny dis w hrt f: -- fd -- Athscl heart disease of native -- Other disorders of lung -- Paroxysmal atrial fibrillation"
        #                     },
        #                     "diagnosis": {
        #                         "pertinentdiagnosisCont": "Hypothyroidism, unspecified -- Mixed hyperlipidemia -- Old myocardial infarction -- Hypokalemia -- Gastro-esophageal reflux disease without esophagitis -- Hypomagnesemia -- Age-related cognitive decline -- Primary generalized (osteo) arthritis -- Vitamin D deficiency, unspecified -- Idiopathic gout, multiple sites -- Age-related osteoporosis w/o current pathological fracture -- Weakness -- Long term (current) use of anticoagulants -- Dependence on supplemental oxygen",
        #                         "constipated": False,
        #                         "painIn": "No where ",
        #                         "depression": False,
        #                         "diabetec": False,
        #                         'oxygen': True
        #                     },
        #                     "medications": {
        #                         "medications": "Ozempic 2 mg/3 ml, inject 0.5 mg subcutaneously daily; Janumet 50-500 mg, 1 tablet by mouth 2 times daily; Atorvastatin 20 mg, 1 tablet by mouth daily; Aspirin EC 81 mg, 1 tablet by mouth daily; Levothyroxine 75 mcg, 1 tablet by mouth daily; Allopurinol 100 mg, 1 tablet by mouth daily; Alendronate 70 mg, 1 tablet by mouth weekly; Omeprazole 40 mg, 1 tablet by mouth daily; Amiodarone HCL 200 mg, 1 tablet by mouth 2 times daily; Hydralazine 50 mg, 1 tablet by mouth 2 times daily as needed for SBP > 160 mmHg; Olmesartan-HCTZ 40-25 mg, 1 tablet by mouth daily; Carvedilol 12.5 mg, 1 tablet by mouth 2 times daily; Clonidine HCL 0.2 mg/day, apply 1 patch weekly; Vitamin D-3 2000 International Units, 1 tablet by mouth daily; Magnesium Oxide 400 mg, 1 tablet by mouth daily; Eliquis 2.5 mg, 1 tablet by mouth 2 times daily; Ipratropium-Albuterol 0.5-3 mg/3 ml vial, use via nebulizer every 6 hours as needed for SOB; Furosemide 20 mg, 1 tablet by mouth daily Monday-Wednesday-Friday; Isosorbide Dinitrate 10 mg, 1 tablet by mouth 2 times daily; Plavix 75 mg, 1 tablet by mouth daily; Potassium Chloride 8 meq, 1 tablet by mouth daily; Oxygen 3L/min via NC continuous; Tylenol 325 mg, 1 tablet by mouth daily as needed for pain",
        #                         "painMedications": "Panadol 100 mg, 1 tablet by mouth daily as needed for pain"
        #                     },
        #                     "extraDetails": {
        #                         "safetyMeasures": "Bleeding precautions, Fall precautions, O2 precautions, Infection control",
        #                         "safetyMeasuresCont": "Clear Pathways",
        #                         "nutritionalReq": "Low Fat",
        #                         "nutritionalReqCont": "Dash",
        #                         "edema": "None",
        #                         "can": False,
        #                         "walker": False,
        #                         "vertigo": True
        #                     }
                            
        #                     }


        submission_data = {
            "action": action,
            "sn_name": sn_name,
            "appointment_dates": formatted_dates,
            "appointment_times": formatted_times,
            "extraction_results": extraction_result,
        }
    
        shared_data.data = submission_data
        print(submission_data)
        # Redirect to the disease analysis page.
        # st.session_state["page"] = "doc"
        st.session_state["page"] = "disease_analysis"
        st.rerun()  # Force the app to rerun so that app.py detects the new page state.
