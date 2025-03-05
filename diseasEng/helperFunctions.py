import time
import json
import logging
from dotenv import load_dotenv
# Load environment variables
load_dotenv()


# Function that sends the request and waits for completion
def wait_for_run_completion(client, assistant_id, disease_name, provided_medications, o2=False, diabetec=False, sleep_interval=5):
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


import json
import logging

import json
import logging

def add_special_conditions(o2_flag, diabetec_flag):
    """Adds condition-specific sentences to text2."""
    conditions = []
    if o2_flag:
        conditions.append("SN instructed patient/PCG on proper oxygen therapy usage and monitoring for complications.")
    if diabetec_flag:
        conditions.append("SN instructed patient/PCG on managing diabetes, including blood sugar monitoring and dietary recommendations.")
    return " ".join(conditions)

def fetch_info_from_gpt(client, query_type, query_value, o2_flag=False, diabetec_flag=False):
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


    # Process disease queries
    if query_type == "disease":
        gpt_prompt = f"""
        You are a highly structured medical assistant.

        TASK: Search for structured medical information on the disease: '{query_value}'. 
        - If the disease name contains a leading code (e.g., "I11.9 Hypertensive heart disease with"), **ignore the code** and use only the disease name.
        - Find a single medication for it
        - Ensure text1 and text2 remain synchronized.

        
        RESPONSE FORMAT (STRICTLY FOLLOW THIS JSON FORMAT):
        {{
          "text1": "Altered status due to [{query_value}]. Knowledge deficit regarding measures to control [{query_value}] and the medication [find a medication with instructions e.g Janumet 50-1000 mg, 1 tablet by mouth 2 times daily] as ordered by MD.",
          "text2": "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [150-200 words description of disease]. .SN instructed Patient/PCG regarding the medication [medication name e.g Janumet 50-1000 mg].  [30-50 word description of medication]. SN advised Patient/PCG to take medication [medication with instructions e.g Janumet 50-1000 mg, 1 tablet by mouth 2 times daily] as ordered by MD."
        }}

        [] is a placeolder that needs to be replaced by the desired information as mentioned inside each brackets.

        
        STRICT GUIDELINES:
        - **Return ONLY valid JSON** (no extra text or formatting outside JSON).
        - **Follow the specified format exactly—do not alter structure or wording.
        - **Exclude unnecessary information (e.g., sources, extra text).
        - **If the disease is not found, return:**
          {{
            "text1": "no disease found in database",
            "text2": "no disease found in database"
          }}
        """

    # Process medication queries
    elif query_type == "medication":
        gpt_prompt = f"""
        You are a highly structured medical assistant.

        TASK: Search for a recommended medication for the disease: '{query_value}'. 
        - If the disease name contains a leading code (e.g., "I11.9 Hypertensive heart disease with"), **ignore the code** and use only the disease name.

        RESPONSE FORMAT (STRICTLY FOLLOW THIS JSON FORMAT):
        {{
          "text1": "Altered status due to [{query_value}]. Knowledge deficit regarding measures to control [{query_value}] and the medication [copy paste medication with instructions] as ordered by MD.",
          "text2": "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [150-200 words description of disease]. .SN instructed Patient/PCG regarding the medication [medication name].  [30-50 word description of medication]. SN advised Patient/PCG to take medication [copy paste medication with instructions] as ordered by MD."
        }}

        STRICT GUIDELINES:
        - **Return ONLY valid JSON** (no extra text or formatting outside JSON).
        - **If no medication is found, return:**
          {{
            "text1": "no medication found in database",
            "text2": "no medication found in database"
          }}
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

        # Extract JSON response
        json_start = gpt_result.find("{")
        json_end = gpt_result.rfind("}")

        if json_start == -1 or json_end == -1:
            logging.error(f"GPT response did not contain valid JSON: {gpt_result}")
            return return_no_data_response(query_type)  # Return fallback response

        json_response = gpt_result[json_start:json_end+1]  # Extract JSON content

        # Parse JSON
        parsed_response = json.loads(json_response)

        # Ensure required fields are present
        if "text1" not in parsed_response or "text2" not in parsed_response:
            logging.error(f"GPT response is missing required fields: {parsed_response}")
            return return_no_data_response(query_type)

        return parsed_response

    except json.JSONDecodeError:
        logging.error(f"❌ JSONDecodeError: Failed to parse GPT response for {query_type}: {query_value}")
        print(f"❌ GPT response was not in correct JSON format:\n{gpt_result}")
        return return_no_data_response(query_type)

    except Exception as e:
        logging.error(f"❌ GPT API Error: {e}")
        return return_no_data_response(query_type)  # Handle general errors
    


    
def fetch_info_from_gpt2(client, query_value, o2_flag=False, diabetec_flag=False):
    """
    Fetches disease or medication information using GPT-4o.
    
    Parameters:
        query_value (str): The disease name or medication name to search for.
        o2_flag (bool): If True, adds the O₂-related sentence to text2.
        diabetec_flag (bool): If True, adds the diabetes-related sentence to text2.
    
    Returns:
        dict: JSON response containing the formatted output.
    """

    gpt_prompt = f"""
    You are a highly structured medical assistant.

    TASK: Search for structured medical information on the disease: '{query_value}'. 
    - If the disease name contains a leading code (e.g., "I11.9 Hypertensive heart disease with"), **ignore the code** and use only the disease name.
    
    RESPONSE FORMAT (STRICTLY FOLLOW THIS JSON FORMAT):
    {{
        "text1": "Altered status due to [{query_value}]. Knowledge deficit regarding measures to control [{query_value}] and the medication //???medication info and usage???// as ordered by MD.",
        "text2": "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [150-200 words description of disease]. .SN instructed Patient/PCG regarding the medication //???medication name???//.  //??medication description 30-50 words???//. SN advised Patient/PCG to take medication //???medication info and usage???// as ordered by MD."
    }}
    
    STRICT GUIDELINES:
    - **Return ONLY valid JSON** (no extra text or formatting outside JSON).
    - **Follow the specified format exactly—do not alter structure or wording.
    - **Exclude unnecessary information (e.g., sources, extra text).
    
    - **If the disease is not found, return:**
        {{
        "text1": "no disease found in database",
        "text2": "no disease found in database"
        }}
    """


    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": gpt_prompt}]
        )

        gpt_result = gpt_response.choices[0].message.content.strip()

        # Log GPT raw response for debugging
        logging.info(f"GPT Raw Response for '{query_value}':\n{gpt_result}")

        # Extract JSON response
        json_start = gpt_result.find("{")
        json_end = gpt_result.rfind("}")

        if json_start == -1 or json_end == -1:
            logging.error(f"GPT response did not contain valid JSON: {gpt_result}")
            return return_no_data_response(" No response")  # Return fallback response

        json_response = gpt_result[json_start:json_end+1]  # Extract JSON content

        # Parse JSON
        parsed_response = json.loads(json_response)

        # Ensure required fields are present
        if "text1" not in parsed_response or "text2" not in parsed_response:
            logging.error(f"GPT response is missing required fields: {parsed_response}")
            return return_no_data_response(" No response")

        return parsed_response

    except json.JSONDecodeError:
        logging.error(f"❌ JSONDecodeError: Failed to parse GPT response for  {query_value}")
        print(f"❌ GPT response was not in correct JSON format:\n{gpt_result}")
        return return_no_data_response(" No response")

    except Exception as e:
        logging.error(f"❌ GPT API Error: {e}")
        return return_no_data_response(" No response")  # Handle general errors
    


    