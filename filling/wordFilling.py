import data.shared_data as shared_data
import streamlit as st
import json
from datetime import datetime
from filling.adjustDates import adjust_dates
from filling.randomValGen import getRangeValuesArray
from filling.docProcessing import process_document_full
# --------------------------
# (Make sure that extractedResults, mainContResponse, and other external variables are defined.)
def fillDoc():
    # Example external variables (replace with your own logic or data)
    extractedResults = shared_data.data['extraction_results']
    constipation = extractedResults['diagnosis']['constipated']
    sn_name = shared_data.data['sn_name']
    appointment_dates = shared_data.data['appointment_dates']
    # Convert raw appointment dates from "DD/MM/YYYY" to "MM/DD/YY"
    # appointment_dates = [
    #     datetime.strptime(date_str, "%d/%m/%Y").strftime("%m/%d/%y")
    #     for date_str in raw_appointment_dates
    # ]
    oxygenFlag = extractedResults['diagnosis']['oxygen']

    print(appointment_dates)
    appointment_times = shared_data.data['appointment_times']
    print(appointment_times)

    dischargeLastPage = {'text1': """Upon today’s assessment patient's condition is stable, vital signs remain stable recently. Patient/PCG monitored with discharge instruction.""",
                         'text2': """SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. SN informed Patient/PCG regarding possible discharge from services next visit. Patient/ PCG instructed re medication regimen -take all prescribed medications as ordered; if a dose is skipped never take double dose; do not stop taking medicine abruptly, keep your medicine in original container. Instructions are: measures to increase activity tolerance -use energy saving techniques, rest frequently during an activity, schedule an activity when most tolerated-after rest periods, after pain meds, at least one hour after meals; put most frequently used items within easy reach; eat a well-balanced diet; set realistic goals.""",
                         }

    # For the dynamic replacement, assume mainContResponse is defined.
    mainContResponse = shared_data.mainContResponse
#     mainContResponse = {
#     "page1": "{\n  \"text1\": \"Altered status due to Type 2 diabetes mellitus. Knowledge deficit regarding measures to control Type 2 diabetes mellitus and the medication Janumet 50-500 mg as ordered by MD.\",\n  \n  \"text2\": \"SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to record blood sugar test results checked by Pt/PCG during the visits and report any significant changes to MD. SN to perform diabetic foot exam upon every visit. PCG assumes DM responsibilities, is confident, capable, and competent in checking blood sugar daily. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication Janumet 50-500 mg as ordered by MD.\"\n}",
#     "page2": "{\n  \"text1\": \"no disease found in database\",\n  \"text2\": \"no disease found in database\"\n}",
#     "page3": "{\n  \"text1\": \"no disease found in database\",\n  \"text2\": \"no disease found in database\"\n}",
#     "page4": "{\n  \"text1\": \"Altered GU status due to chronic kidney disease. Knowledge deficit regarding chronic kidney disease.\",\n  \"text2\": \"SN instructed regarding chronic kidney disease. Chronic kidney disease (CKD) means your kidneys are damaged and can't filter blood the way they should. The disease is called \u201cchronic\u201d because the damage to your kidneys happens slowly over a long period of time. This damage can cause waste to build up in your body. CKD can also cause other health problems. Often, though, chronic kidney disease has no cure. Treatment usually consists of measures to help control signs and symptoms, reduce complications, and slow progression of the disease. If your kidneys become severely damaged, you may need treatment for end-stage kidney disease. SN advised Patient/PCG to take medication Furosemide 20 mg as ordered by MD.\"\n}",
#     "page5": "{\n  \"text1\": \"Altered cardiovascular status due to Athscl heart disease of native coronary artery w/o angina pectoris. Knowledge deficit regarding measures to control Athscl heart disease of native coronary artery w/o angina pectoris and the medication Aspirin 81 mg as ordered by MD.\",\n  \n  \"text2\": \"SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication Aspirin 81 mg as ordered by MD.\"\n}",
#     "page6": "{\n  \"text1\": \"Altered respiratory status due to other disorders of lung. Knowledge deficit regarding measures to control other disorders of lung and the medication Albuterol 90 mcg as ordered by MD.\",\n  \n  \"text2\": \"SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication Albuterol 90 mcg as ordered by MD.\"\n}",
#     "page7": "{\n  \"text1\": \"Altered respiratory status due to other disorders of lung. Knowledge deficit regarding measures to control other disorders of lung and the medication Albuterol 90 mcg as ordered by MD.\",\n  \n  \"text2\": \"SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication Albuterol 90 mcg as ordered by MD.\"\n}",
#     "page8": "{\n  \"text1\": \"Altered respiratory status due to other disorders of lung. Knowledge deficit regarding measures to control other disorders of lung and the medication Albuterol 90 mcg as ordered by MD.\",\n  \n  \"text2\": \"SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication Albuterol 90 mcg as ordered by MD.\"\n}",
#     "page9": "{\n  \"text1\": \"Altered respiratory status due to other disorders of lung. Knowledge deficit regarding measures to control other disorders of lung and the medication Albuterol 90 mcg as ordered by MD.\",\n  \n  \"text2\": \"SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication Albuterol 90 mcg as ordered by MD.\"\n}",
#     "page10": "{\n  \"text1\": \"Altered respiratory status due to other disorders of lung. Knowledge deficit regarding measures to control other disorders of lung and the medication Albuterol 90 mcg as ordered by MD.\",\n  \n  \"text2\": \"SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [rest of the info]. SN advised Patient/PCG to take medication Albuterol 90 mcg as ordered by MD.\"\n}",
# }

    wordFileName = './noteTemplates/1-page-version copy.docx'  # Ensure this file exists in your working directory


    # Get Action
    getAction = shared_data.data['action'] 
    if getAction == "Reset":
        valuesToGet = 9
        # wordFileName = './noteTemplates/9-page-version.docx'  # Ensure this file exists in your working directory
    elif getAction == "Discharge":
        valuesToGet = 10
        # wordFileName = './noteTemplates/10-page-version.docx'  # Ensure this file exists in your working directory
        mainContResponse['page10'] = json.dumps(dischargeLastPage)

    # Generate arrays for 10 iterations.
    tempArray = []
    hrArray = []
    rrArray = []
    oxygenArray = []
    bsFastArray = []
    bsRapidArray = []
    random_bpArray = []

    tempArray, hrArray, rrArray, oxygenArray, bsFastArray, bsRapidArray, random_bpArray = getRangeValuesArray(valuesToGet)

    if extractedResults['extraDetails']['can'] == True and extractedResults['extraDetails']['walker'] == True:
        canWalkerText = 'can, walker'
    elif extractedResults['extraDetails']['can'] == True and extractedResults['extraDetails']['walker'] == False:
        canWalkerText = 'can'
    elif extractedResults['extraDetails']['can'] == False and extractedResults['extraDetails']['walker'] == True:
        canWalkerText = 'walker'
    else:
        canWalkerText = ''

    painScaleArray = ['5/10', '4/10', '4/10', '4/10', '4/10', '3/10', '3/10', '3/10', '2/10']

    if getAction == "Discharge":
        painScaleArray.append('4/10')

    output_files = []
    for i in range(valuesToGet):
        headerPage = extractedResults['patientDetails']['providerName']

        # Extract the starting time from the appointment time string
        time_str = appointment_times[i]
        start_time_str = time_str.split('-')[0].strip() if '-' in time_str else time_str.strip()

        if datetime.strptime(start_time_str, "%H:%M") < datetime.strptime("10:00", "%H:%M"):
            bsValue = bsFastArray[i]
        else:
            bsValue = bsRapidArray[i]

        replacements_first_col = {
            'cane, walker': canWalkerText,
            'Pain in Lower back, Neck, Joints': extractedResults['diagnosis']['painIn'],
            '4/10': painScaleArray[i],
            'tpainmedhere': extractedResults['medications']['painMedications'],
            '05/07/23': adjust_dates(appointment_dates[i], appointment_times[i], constipation),
            'NAS, Controlled carbohydrate Low fat, Low cholesterol, NCS, Dash': extractedResults['extraDetails']['nutritionalReq'] + ", " + extractedResults['extraDetails']['nutritionalReqCont']
            }
        # Conditionally add the oxygen value only if oxygenFlag is True
        if oxygenFlag:
            replacements_first_col['OXVAL)('] = oxygenArray[i]+ "%"
        else:
            replacements_first_col['OXVAL)('] = ""

        replacements_second_col = {
            'T- 96.8': "T- " + tempArray[i],
            'HR- 66': "HR- " + hrArray[i],
            'RR -16': "RR - " + rrArray[i],
            'BS 198': "BS " + bsValue,
            'Sitting 142/89': "Sitting " + random_bpArray[i],
            'PARKER, PETER/LVN': sn_name,
            'MR# 022-001': "MR# " + extractedResults['patientDetails']['medicalRecordNo'][-7:],
            'PORK, JOHN': extractedResults['patientDetails']["name"],
            '05/08/2023': datetime.strptime(appointment_dates[i], "%d/%m/%Y").strftime("%m/%d/%y"),
            '18:00-18:45': appointment_times[i],
            'new text1': json.loads(mainContResponse.get(f'page{i+1}', '{}')).get("text1", ""),
            'replacement text': json.loads(mainContResponse.get(f'page{i+1}', '{}')).get("text2", ""),

        }

        dm2_value =  extractedResults['diagnosis']['diabetec']
        depressed_value = extractedResults['diagnosis']['depression']
        allSafetyMeasures = extractedResults['extraDetails']['safetyMeasures'] + ","  + extractedResults['extraDetails']['safetyMeasuresCont']
        edemaResults = extractedResults['extraDetails']['edema']

    
        out_file = process_document_full(
            wordFileName, headerPage, replacements_first_col, replacements_second_col,
            allSafetyMeasures, dm2_value, edemaResults, depressed_value, i, getAction, valuesToGet
        )
        output_files.append(out_file)

    for file in output_files:
        with open(file, "rb") as doc_file:
            st.download_button(
                label=f"Download {file}",
                data=doc_file,
                file_name=file,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    # # Process the document and get the output filename.
    # output_file = process_document_full(wordFileName, headerPage, replacements_first_col, replacements_second_col, 
    #                                     allSafetyMeasures, dm2_value, edemaResults, depressed_value)

    # # Provide a download button using Streamlit.
    # with open(output_file, "rb") as doc_file:
    #     st.download_button(
    #         label="Download Modified Document",
    #         data=doc_file,
    #         file_name=output_file,
    #         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    #     )
