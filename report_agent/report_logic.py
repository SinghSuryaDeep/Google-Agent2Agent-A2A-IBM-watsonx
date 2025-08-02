"""
Author: SURYA DEEP SINGH
LinkedIn: https://www.linkedin.com/in/surya-deep-singh-b9b94813a/
Medium: https://medium.com/@SuryaDeepSingh
GitHub: https://github.com/SinghSuryaDeep
"""

## report_logic.py
from typing_extensions import TypedDict
from pydantic import BaseModel
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langchain_ibm import WatsonxToolkit
from langchain_ibm.chat_models import ChatWatsonx
import json
import os
from dotenv import load_dotenv
load_dotenv()
url=os.getenv("WATSONX_URL")
project_id=os.getenv("WATSONX_PROJECT_ID")
apikey=os.getenv("WATSONX_APIKEY")
model_id=os.getenv("WATSONX_MODEL")

class ReportState(TypedDict):
    diagnosis: dict
    formatted: str

class FormatInput(BaseModel):
    diagnosis: dict

watsonx = WatsonxToolkit(
    url=url,
    project_id=project_id,
    apikey=apikey
)
chat = ChatWatsonx(
    watsonx_client=watsonx.watsonx_client,
    model_id=model_id,
    temperature=0.0,
)

@tool("format_report", args_schema=FormatInput,
      description="Generate JSON report from a diagnosis dict")
def format_report(diagnosis: dict) -> str:
    cond = diagnosis.get("condition", "Unknown")
    risk = diagnosis.get("risk", "Unknown")
    report = {
        "Condition": cond,
        "RiskLevel": risk,
        "Recommendations": [
            "Follow up in 2 weeks",
            "Monitor vitals daily"
        ]
    }
    return json.dumps(report, indent=2)

def create_report_graph():
    graph = StateGraph(ReportState)

    def agent_node(state: ReportState) -> dict:
        prompt = f"Format this diagnosis as structured JSON:\n{state['diagnosis']}"
        res = chat.invoke([{"role": "user", "content": prompt}])
        return {"formatted": res.content}

    def format_node(state: ReportState) -> dict:
        s = format_report.invoke({"diagnosis": state["diagnosis"]})
        return {"formatted": s}

    graph.add_node("agent", agent_node)
    graph.add_node("format", format_node)
    graph.set_entry_point("agent")
    graph.add_edge("agent", "format")
    graph.set_finish_point("format")
    return graph.compile()
