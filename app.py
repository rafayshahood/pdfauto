import streamlit as st
import tempfile
import sys
from dotenv import load_dotenv
from unstract.llmwhisperer import LLMWhispererClientV2
from unstract.llmwhisperer.client import LLMWhispererClientException
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from datetime import datetime
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
import os
import json

# Load environment variables from .env file
load_dotenv()
# Access the LLM Whisperer API key
llm_api_key = os.getenv('LLMWHISPERER_API_KEY')
# Access the open ai  API key
openai_api_key = os.getenv('OPENAI_API_KEY')

# Predefined credentials
correct_username = "Davit"
correct_password = "davitautomation"

# Define the models
class PatientDetails(BaseModel):
    name: str = Field(description="Patient's Name and Address of the individual")
    medicalRecordNo: str = Field(description="Medical Record No. of the individual")
    providerName: datetime = Field(description="Provider's Name, Address, and Telephone Number")
    diagnosis: str = Field(description="Principal Diagnosis of the individual")


class ExtraDetails(BaseModel):
    medications: str = Field(description="10. Medications: Dose/Frequency/Route (N)ew (C)hanged")
    safetyMeasures: str = Field(description="15. Safety Measures")
    nutritionalReq: str = Field(description="16. Nutritional Req")
    painIn: str = Field(description="Pain in which parts of the patient")
    painMedication: str = Field(description="Is there a pain medication recommended? If yes name it")
    edema: str = Field(description="Edema Management")


class Form485(BaseModel):
    patientDetails: PatientDetails = Field(description="Personal details of the patient")
    extra_details: ExtraDetails = Field(description="Extra details of the patient")

# Error handler for exceptions
def error_exit(error_message):
    sys.exit(1)

def process_485_information(extracted_text):
    preamble = ("What you are seeing is a filled out Home health Health Certification and Plan of care form. Your job is to extract the "
                "information from it accurately.")
    postamble = "Do not include any explanation in the reply. Only include the extracted information in the reply."
    system_template = "{preamble}"
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = "{format_instructions}\n\n{extracted_text}\n\n{postamble}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    parser = PydanticOutputParser(pydantic_object=Form485)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    request = chat_prompt.format_prompt(preamble=preamble,
                                        format_instructions=parser.get_format_instructions(),
                                        extracted_text=extracted_text,
                                        postamble=postamble).to_messages()
    chat = ChatOpenAI(model="gpt-4o-mini")
    response = chat(request, temperature=0.0)

    # Clean the response to remove Markdown code block formatting
    response_text = response.content
    response_text_cleaned = response_text.replace("```json", "").replace("```", "").strip()

    try:
        # Attempt to parse the cleaned JSON response
        response_json = json.loads(response_text_cleaned)
        return response_json
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON: {e}")
        return {}

# Extract text from PDF
def extract_text_from_pdf(file_path):
    llmw = LLMWhispererClientV2(api_key = llm_api_key)
    try:
        result = llmw.whisper(file_path=file_path, wait_for_completion=True, wait_timeout=200)
        extracted_text = result["extraction"]
        return extracted_text
    except LLMWhispererClientException as e:
        error_exit(e)

# Process the uploaded PDF
def process_485_pdf(file_path):
    extracted_text = extract_text_from_pdf(file_path)
    response = process_485_information(extracted_text)
    return response

# Sign-in page
def sign_in():
    st.title("Sign In Page")
    with st.form(key='login_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Sign In")

    if submit_button:
        if username == correct_username and password == correct_password:
            st.success(f"Welcome, {username}!")
            st.session_state.logged_in = True
        elif username == correct_username:
            st.error("Incorrect password. Please try again.")
        else:
            st.error("Incorrect username. Please try again.")

def pdf_upload_page():
    st.title("Upload PDF Page")
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file is not None:
        # Check file size (limit to 200MB)
        file_size = uploaded_file.size / (1024 * 1024)  # MB
        if file_size > 200:
            st.error(f"File is too large! Please upload a file less than 200 MB. Your file is {file_size:.2f} MB.")
        else:
            # Save the uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

            # Process the uploaded PDF
            st.write("Processing PDF...")
            result = process_485_pdf(tmp_file_path)
            
            # Display the extracted data
            st.write("Extracted Data:")
            st.json(result)

            # Generate the JSON file for download
            json_data = json.dumps(result, indent=4)

            # Add download button
            st.download_button(
                label="Download Output as JSON",
                data=json_data,
                file_name="extracted_data.json",
                mime="application/json"
            )

# Main function
def main():
    if 'logged_in' not in st.session_state:
        sign_in()  # If not logged in, show the sign-in page
    elif st.session_state.logged_in:
        pdf_upload_page()  # If logged in, show the PDF upload page

if __name__ == "__main__":
    main()