"""
Author: SURYA DEEP SINGH
LinkedIn: https://www.linkedin.com/in/surya-deep-singh-b9b94813a/
Medium: https://medium.com/@SuryaDeepSingh
GitHub: https://github.com/SinghSuryaDeep
"""
# # # diagnostics_logic.py
import asyncio
import json
import logging
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base._task import TaskResult
from autogen_watsonx_client.config import WatsonxClientConfiguration
from autogen_watsonx_client.client import WatsonXChatCompletionClient
import os
from dotenv import load_dotenv
load_dotenv()
url=os.getenv("WATSONX_URL")
project_id=os.getenv("WATSONX_PROJECT_ID")
apikey=os.getenv("WATSONX_APIKEY")
model_id=os.getenv("WATSONX_MODEL")

wx_config = WatsonxClientConfiguration(
    project_id=project_id,
    url=url,
    api_key=apikey,
    model_id=model_id
)
watsonx_client = WatsonXChatCompletionClient(**wx_config)

async def analyze_patient_data_async(patient_data: dict) -> TaskResult:

    symptoms = ", ".join(patient_data.get("symptoms", []))
    vitals = patient_data.get("vitals", {})

    diagnostic_agent = AssistantAgent(
        name="Diagonstic_agent",
        model_client=watsonx_client
    )
    termination = TextMentionTermination("TERMINATE")

    team = RoundRobinGroupChat(
        [diagnostic_agent],
        termination_condition=termination
    )

    
    # Define prompt
    prompt = f"""
    Analyze the following patient data:
    Symptoms: {symptoms}
    Vitals: {vitals}

    Your task is to provide a probable diagnosis and an associated risk level (Low, Medium, or High).
    Your response MUST BE ONLY the following JSON object. Do not include any other text, greetings, or explanations.

    ```json
    {{
      "condition": "A probable condition based on the data",
      "risk": "Low/Medium/High"
    }}
    ```
    """

    return await team.run(task=prompt)


# JSON extractor from TaskResult
def extract_json_from_message(task_result: TaskResult) -> dict:
    if not task_result.messages:
        return {}

    for message in reversed(task_result.messages):
        if isinstance(message, TextMessage) and message.source == "Diagonstic_agent":
            content = message.content
            start_tag, end_tag = '```json', '```'

            start_index = content.find(start_tag)
            if start_index != -1:
                json_start = start_index + len(start_tag)
                json_end = content.find(end_tag, json_start)
                if json_end != -1:
                    json_str = content[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
    return {}

# Sync wrapper for API use
def analyze_patient_data(patient_data: dict) -> dict:
    try:
        task_result = asyncio.run(analyze_patient_data_async(patient_data))
        return extract_json_from_message(task_result)
    except Exception as e:
        logging.exception("Error during analysis")
        return {"error": str(e), "status": "failed"}

