import streamlit as st
import tempfile
import sys
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

import shared_data
from diseaseEngine import process_diseases
from extraction import main as extractionMain

def load_extraction_data(filepath="extraction_results.json"):
    with open(filepath, "r") as f:
        data = json.load(f)
    return data

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
        
        if action == "Reset":
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

        
        formatted_dates = [d.strftime("%d/%m/%Y") for d in appointment_dates]
        formatted_times = []
        for t in appointment_times:
            dt = datetime.combine(datetime.today(), t)
            end_dt = dt + timedelta(minutes=45)
            start_str = dt.strftime("%I:%M").lstrip("0")
            end_str = end_dt.strftime("%I:%M").lstrip("0")
            formatted_times.append(f"{start_str}-{end_str}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name

        extraction_result = extractionMain(tmp_file_path)

        submission_data = {
            "action": action,
            "sn_name": sn_name,
            "appointment_dates": formatted_dates,
            "appointment_times": formatted_times,
            "extraction_results": extraction_result
        }
        shared_data.data = submission_data
        # Redirect to the disease analysis page.
        st.session_state["page"] = "disease"
        st.rerun()  # Force the app to rerun so that app.py detects the new page state.
