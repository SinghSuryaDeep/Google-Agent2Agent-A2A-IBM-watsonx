"""
Author: SURYA DEEP SINGH
LinkedIn: https://www.linkedin.com/in/surya-deep-singh-b9b94813a/
Medium: https://medium.com/@SuryaDeepSingh
GitHub: https://github.com/SinghSuryaDeep
"""
# admin_agent/server.py

from flask import Flask, request, jsonify
import asyncio
import logging
from admin_logic import schedule_followup

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A2A Compliant Agent Card
agent_card = {
    "apiVersion": "a2a/v0.2",
    "kind": "AgentCard",
    "metadata": {
        "id": "admin-agent",
        "name": "AdminAgent",
        "description": "Schedules patient follow-up appointments based on medical reports.",
        "version": "1.0.0",
        "tags": ["healthcare", "scheduling", "admin"]
    },
    "spec": {
        "url": "http://127.0.0.1:8003",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "interactionModes": ["synchronous"]
        },
        "authentication": {
            "schemes": ["none"]
        },
        "skills": [
            {
                "id": "schedule-followup",
                "name": "Schedule Follow-up",
                "description": "Schedule a follow-up appointment based on medical report",
                "tags": ["scheduling", "admin", "healthcare"],
                "examples": [
                    {
                        "description": "Schedule based on hypertension report",
                        "input": {
                            "report": "{\n  \"Condition\": \"Hypertension\",\n  \"RiskLevel\": \"Medium\",\n  \"Recommendations\": [\n    \"Follow up in 2 weeks\",\n    \"Monitor vitals daily\"\n  ]\n}"
                        },
                        "output": {
                            "appointment_info": {
                                "appointment": "2025-06-25T10:00:00Z",
                                "link": "https://example.com/appointment"
                            }
                        }
                    }
                ],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "report": {
                            "type": "string",
                            "description": "Medical report in JSON format"
                        }
                    },
                    "required": ["report"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "appointment_info": {
                            "type": "object",
                            "properties": {
                                "appointment": {"type": "string"},
                                "link": {"type": "string"}
                            },
                            "required": ["appointment"]
                        }
                    },
                    "required": ["appointment_info"]
                },
                "invocation": {
                    "method": "POST",
                    "endpoint": "/skills/schedule-followup",
                    "contentType": "application/json"
                }
            }
        ]
    }
}

@app.route("/.well-known/agent.json", methods=["GET"])
def agent_manifest():
    """A2A Agent Discovery Endpoint"""
    return jsonify(agent_card)

@app.route("/skills/schedule-followup", methods=["POST"])
def schedule_followup_skill():
    """A2A Compliant Skill Invocation"""
    try:
        request_data = request.json
        if not all(key in request_data for key in ["jsonrpc", "method", "params", "id"]):
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request - Missing required JSON-RPC fields"
                },
                "id": request_data.get("id")
            }), 400
        
        if request_data["jsonrpc"] != "2.0":
            return jsonify({
                "jsonrpc": "2.0", 
                "error": {
                    "code": -32600,
                    "message": "Invalid Request - jsonrpc must be '2.0'"
                },
                "id": request_data.get("id")
            }), 400
            
        if request_data["method"] != "invoke":
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {request_data['method']}"
                },
                "id": request_data["id"]
            }), 404
        
        # Extract parameters
        params = request_data.get("params", {})
        report = params.get("report")
        
        if not report:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params - Missing 'report'"
                },
                "id": request_data["id"]
            }), 400
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            appointment_info = loop.run_until_complete(schedule_followup(report))
        finally:
            loop.close()
        return jsonify({
            "jsonrpc": "2.0",
            "result": {
                "appointment_info": appointment_info
            },
            "id": request_data["id"]
        })
        
    except Exception as e:
        logger.exception("Error during skill invocation")
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            },
            "id": request_data.get("id") if request_data else None
        }), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "protocol": "A2A v0.2"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8003, debug=True)