"""
Author: SURYA DEEP SINGH
LinkedIn: https://www.linkedin.com/in/surya-deep-singh-b9b94813a/
Medium: https://medium.com/@SuryaDeepSingh
GitHub: https://github.com/SinghSuryaDeep
"""

import asyncio
from beeai_framework.agents.react import ReActAgent
from beeai_framework.adapters.watsonx import WatsonxChatModel
from beeai_framework.memory.token_memory import TokenMemory
from beeai_framework.tools.code import LocalPythonStorage, PythonTool
import re
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()
url=os.getenv("WATSONX_URL")
project_id=os.getenv("WATSONX_PROJECT_ID")
apikey=os.getenv("WATSONX_APIKEY")
model_id=os.getenv("WATSONX_MODEL")


def create_admin_agent():
    llm = WatsonxChatModel(
        api_key=apikey,
        project_id=project_id,
        model=model_id,
        url=url,
        # Add these parameters to improve output consistency
        temperature=0.1,  # Lower temperature for more consistent output
        max_tokens=1000,
        top_p=0.9
    )
    
    memory = TokenMemory(llm=llm)
    storage = LocalPythonStorage(
        local_working_dir=os.getenv("CODE_INTERPRETER_SOURCE", "./tmp/source"),
        interpreter_working_dir=os.getenv("CODE_INTERPRETER_TMPDIR", "./tmp/target"),
    )
    python_tool = PythonTool(
        code_interpreter_url=os.getenv("CODE_INTERPRETER_URL", "http://127.0.0.1:50081"),
        storage=storage,
    )
    
    agent = ReActAgent(llm=llm, memory=memory, tools=[python_tool])
    return agent

async def schedule_followup(report: str) -> dict:
    agent = create_admin_agent()
    
    
    # Parse the report to extract key information
    try:
        report_data = json.loads(report)
        condition = report_data.get("Condition", "Unknown")
        risk_level = report_data.get("RiskLevel", "Unknown")
        recommendations = report_data.get("Recommendations", [])
    except json.JSONDecodeError:
        # Fallback if report is not JSON
        condition = "Unknown"
        risk_level = "Unknown"
        recommendations = []
    
    # Create a more structured prompt
    prompt = f"""You are a healthcare administrative assistant. Your task is to schedule a follow-up appointment based on a medical report.

Medical Report Details:
- Condition: {condition}
- Risk Level: {risk_level}
- Recommendations: {', '.join(recommendations)}

Your task:
1. First, analyze the medical report and determine an appropriate follow-up timeframe
2. Calculate a specific follow-up datetime (use current date + appropriate interval)
3. Generate a calendar event URL for the appointment
4. Provide the final URL

Please think step by step and use the Python tool to:
- Calculate the appropriate follow-up date
- Generate a calendar event URL
- Print the final URL

Focus on providing a clear, actionable result."""

    try:
        result = await agent.run(prompt=prompt)
        # Extract the result more robustly
        output = None
        if hasattr(result, 'answer') and hasattr(result.answer, 'text'):
            output = result.answer.text
        elif hasattr(result, 'final_answer'):
            output = result.final_answer
        elif hasattr(result, 'text'):
            output = result.text
        else:
            output = str(result)
        
        # Extract URL if present
        match = re.search(r"https?://\S+", output or "")
        link = match.group(0) if match else None
        
        # Provide a fallback date calculation
        followup_date = datetime.now() + timedelta(days=14)  # Default 2 weeks
        if "2 weeks" in str(recommendations):
            followup_date = datetime.now() + timedelta(days=14)
        elif risk_level == "High":
            followup_date = datetime.now() + timedelta(days=7)  # 1 week for high risk
        
        return {
            "appointment": followup_date.isoformat() + "Z",
            "link": link or f"https://calendar.google.com/calendar/event?action=TEMPLATE&text=Follow-up%20Appointment&dates={followup_date.strftime('%Y%m%dT%H%M%S')}/{followup_date.strftime('%Y%m%dT%H%M%S')}"
        }
        
    except Exception as e:
        print(f"Error in agent execution: {str(e)}")
        # Fallback response
        fallback_date = datetime.now() + timedelta(days=14)
        return {
            "appointment": fallback_date.isoformat() + "Z",
            "link": f"https://calendar.google.com/calendar/event?action=TEMPLATE&text=Follow-up%20Appointment&dates={fallback_date.strftime('%Y%m%dT%H%M%S')}/{fallback_date.strftime('%Y%m%dT%H%M%S')}"
        }

# Alternative approach: Direct implementation without ReAct agent
def schedule_followup_direct(report: str) -> dict:
    """
    Direct implementation without ReAct agent to avoid parsing issues
    """
    try:
        # Parse the report
        report_data = json.loads(report)
        condition = report_data.get("Condition", "Unknown")
        risk_level = report_data.get("RiskLevel", "Unknown")
        recommendations = report_data.get("Recommendations", [])
        
        # Determine follow-up timeframe
        if risk_level.lower() == "high":
            days_ahead = 7  # 1 week for high risk
        elif "2 weeks" in str(recommendations).lower():
            days_ahead = 14  # 2 weeks as recommended
        else:
            days_ahead = 14  # Default 2 weeks
        
        # Calculate follow-up date
        followup_date = datetime.now() + timedelta(days=days_ahead)
        
        # Generate calendar URL
        event_title = f"Follow-up: {condition}"
        calendar_url = f"https://calendar.google.com/calendar/event?action=TEMPLATE&text={event_title.replace(' ', '%20')}&dates={followup_date.strftime('%Y%m%dT%H%M%S')}/{followup_date.strftime('%Y%m%dT%H%M%S')}"
        
        return {
            "appointment": followup_date.isoformat() + "Z",
            "link": calendar_url
        }
        
    except Exception as e:
        print(f"Error in direct scheduling: {str(e)}")
        # Fallback
        fallback_date = datetime.now() + timedelta(days=14)
        return {
            "appointment": fallback_date.isoformat() + "Z",
            "link": f"https://calendar.google.com/calendar/event?action=TEMPLATE&text=Follow-up%20Appointment&dates={fallback_date.strftime('%Y%m%dT%H%M%S')}/{fallback_date.strftime('%Y%m%dT%H%M%S')}"
        }