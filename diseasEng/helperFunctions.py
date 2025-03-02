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

    if query_type == "disease":
        gpt_prompt = f"""
        You are a **highly structured medical assistant** with access to **internet-based research and medical knowledge**.

        **TASK:** Search the internet or use your existing knowledge to retrieve structured medical information for the disease: '{query_value}'.

        **Response Format (STRICTLY FOLLOW THIS JSON FORMAT):**
        ```json
        {{
          "text1": "Altered status due to {query_value}. Knowledge deficit regarding measures to control {query_value} and the medication [insert medication] as ordered by MD.",
          "text2": "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. {add_special_conditions(o2_flag, diabetec_flag)}SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [Include a detailed disease summary of approximately 150–200 words that covers the disease’s causes, symptoms, diagnostic findings, and additional relevant clinical details]. SN advised Patient/PCG to take medication [insert medication] as ordered by MD."
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
          "text2": "SN admitted the patient for comprehensive skilled nursing assessment, observation and evaluation of all body systems. SN to assess vital signs, pain level. SN performed to check vital signs and scale pain (1-10) every visit. {add_special_conditions(o2_flag, diabetec_flag)}SN to evaluate therapeutic response to current/new medications and compliance to medication/diet regimen, home safety issues and psychosocial adjustment. [Include a detailed disease summary of approximately 150–200 words that covers the disease’s causes, symptoms, diagnostic findings, and additional relevant clinical details]. SN advised Patient/PCG to take medication [insert medication] as ordered by MD."
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