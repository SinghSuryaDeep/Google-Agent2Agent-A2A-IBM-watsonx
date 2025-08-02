"""
Author: SURYA DEEP SINGH
LinkedIn: https://www.linkedin.com/in/surya-deep-singh-b9b94813a/
Medium: https://medium.com/@SuryaDeepSingh
GitHub: https://github.com/SinghSuryaDeep
"""
# workflow_client.py

import asyncio
import logging
from uuid import uuid4
import httpx
from typing import Any, Optional, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class A2AClient:
    """A2A Protocol Compliant Client"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.agent_card = None
        
    async def discover_agent(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Discover agent capabilities via A2A agent card"""
        agent_card_url = f"{self.base_url}/.well-known/agent.json"
        logger.info(f"Discovering agent at: {agent_card_url}")
        
        response = await client.get(agent_card_url)
        response.raise_for_status()
        
        self.agent_card = response.json()
        logger.info(f"Discovered agent: {self.agent_card['metadata']['name']}")
        logger.info(f"Protocol version: {self.agent_card.get('apiVersion', 'Unknown')}")
        
        return self.agent_card
    
    def find_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Find a skill by ID in the agent card"""
        if not self.agent_card:
            raise ValueError("Agent not discovered yet. Call discover_agent() first.")
            
        for skill in self.agent_card.get("spec", {}).get("skills", []):
            if skill.get("id") == skill_id:
                return skill
        return None
    
    async def invoke_skill(self, client: httpx.AsyncClient, skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a skill using A2A JSON-RPC 2.0 protocol"""
        skill = self.find_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill '{skill_id}' not found")
        
        # Build endpoint URL
        agent_url = self.agent_card.get("spec", {}).get("url", self.base_url)
        endpoint = skill["invocation"]["endpoint"]
        full_url = f"{agent_url.rstrip('/')}{endpoint}"
        
        # Create JSON-RPC 2.0 request
        request_payload = {
            "jsonrpc": "2.0",
            "method": "invoke",
            "params": params,
            "id": str(uuid4())
        }
        
        logger.info(f"Invoking skill '{skill_id}' at {full_url}")
        logger.debug(f"Request payload: {request_payload}")
        
        # Send request
        response = await client.post(
            full_url, 
            json=request_payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Validate JSON-RPC 2.0 response
        if "jsonrpc" not in response_data or response_data["jsonrpc"] != "2.0":
            raise ValueError("Invalid JSON-RPC 2.0 response")
            
        if "error" in response_data:
            error = response_data["error"]
            raise Exception(f"Skill invocation failed: {error.get('message', 'Unknown error')} (Code: {error.get('code')})")
        
        return response_data.get("result", {})

def discover_agent_url(agent_name: str) -> str:
    """Agent discovery mapping"""
    agent_urls = {
        'diagnostics-agent': 'http://127.0.0.1:8001',
        'report-agent': 'http://127.0.0.1:8002',
        'admin-agent': 'http://127.0.0.1:8003'
    }
    return agent_urls.get(agent_name, f"http://127.0.0.1:8001")

async def main():
    """A2A Protocol Multi-Agent Workflow"""
    async with httpx.AsyncClient() as client:
        try:
            conversation_id = str(uuid4())
            logger.info(f"Starting A2A workflow with conversation ID: {conversation_id}")

            # Step 1: Diagnostics Agent
            logger.info("Step 1: Invoking Diagnostics Agent")
            diag_client = A2AClient(discover_agent_url("diagnostics-agent"))
            await diag_client.discover_agent(client)
            
            patient_data = {
                "symptoms": ["headache", "dizziness", "chest pain"],
                "vitals": {"bp": "150/95", "pulse": 90, "temperature": "99.2 F"}
            }
            
            diag_params = {"patient_data": patient_data}
            diag_result = await diag_client.invoke_skill(client, "analyze-patient-data", diag_params)
            diagnosis = diag_result.get("diagnosis", {})
            
            print(f"\n🩺 [Diagnostics] Result:")
            print(f"   • Condition: {diagnosis.get('condition', 'N/A')}")
            print(f"   • Risk Level: {diagnosis.get('risk', 'N/A')}")

            # Step 2: Report Agent
            logger.info("Step 2: Invoking Report Agent")
            report_client = A2AClient(discover_agent_url("report-agent"))
            await report_client.discover_agent(client)
            
            report_params = {"diagnosis": diagnosis}
            report_result = await report_client.invoke_skill(client, "generate-report", report_params)
            report = report_result.get("report", "")
            
            print(f"\n📄 [Report] Generated:")
            print(f"   {report}")

            # Step 3: Admin Agent
            logger.info("Step 3: Invoking Admin Agent")
            admin_client = A2AClient(discover_agent_url("admin-agent"))
            await admin_client.discover_agent(client)
            
            admin_params = {"report": report}
            admin_result = await admin_client.invoke_skill(client, "schedule-followup", admin_params)
            appointment_info = admin_result.get("appointment_info", {})
            
            print(f"\n📅 [Admin] Appointment Scheduled:")
            print(f"   • Date: {appointment_info.get('appointment', 'N/A')}")
            print(f"   • Link: {appointment_info.get('link', 'N/A')}")

            print(f"\n✅ A2A Workflow completed successfully!")
            print(f"   Conversation ID: {conversation_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP Error: {e.response.status_code}")
            try:
                error_details = e.response.json()
                logger.error(f"Error details: {error_details}")
            except:
                logger.error(f"Error response: {e.response.text}")
        except Exception as e:
            logger.exception(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())