"""
Author: SURYA DEEP SINGH
LinkedIn: https://www.linkedin.com/in/surya-deep-singh-b9b94813a/
Medium: https://medium.com/@SuryaDeepSingh
GitHub: https://github.com/SinghSuryaDeep
"""
# report_agent/server.py

import logging
from flask import Flask, request, jsonify
from report_logic import create_report_graph
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
agent_card = {
    "apiVersion": "a2a/v0.2",
    "kind": "AgentCard",
    "metadata": {
        "id": "report-agent",
        "name": "ReportAgent", 
        "description": "Generates medical reports from diagnostic results.",
        "version": "1.0.0",
        "tags": ["healthcare", "reporting", "medical"]
    },
    "spec": {
        "url": "http://127.0.0.1:8002",
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
                "id": "generate-report",
                "name": "Generate Patient Report",
                "description": "Create a human-readable report from diagnosis data",
                "tags": ["reporting", "healthcare", "medical-reports"],
                "examples": [
                    {
                        "description": "Generate report from diagnosis",
                        "input": {
                            "diagnosis": {
                                "condition": "Hypertension",
                                "risk": "Medium"
                            }
                        },
                        "output": {
                            "report": "{\n  \"Condition\": \"Hypertension\",\n  \"RiskLevel\": \"Medium\",\n  \"Recommendations\": [\n    \"Follow up in 2 weeks\",\n    \"Monitor vitals daily\"\n  ]\n}"
                        }
                    }
                ],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "diagnosis": {
                            "type": "object",
                            "properties": {
                                "condition": {"type": "string"},
                                "risk": {"type": "string", "enum": ["Low", "Medium", "High"]}
                            },
                            "required": ["condition", "risk"]
                        }
                    },
                    "required": ["diagnosis"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "report": {"type": "string"}
                    },
                    "required": ["report"]
                },
                "invocation": {
                    "method": "POST",
                    "endpoint": "/skills/generate-report",
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

@app.route("/skills/generate-report", methods=["POST"])
def generate_report_skill():
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
        params = request_data.get("params", {})
        diagnosis = params.get("diagnosis")
        
        if not diagnosis:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params - Missing 'diagnosis'"
                },
                "id": request_data["id"]
            }), 400
        graph = create_report_graph()
        final_state = graph.invoke({"diagnosis": diagnosis})
        report = final_state.get("formatted", None)
        
        if report is None:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error - Report generation failed"
                },
                "id": request_data["id"]
            }), 500
        return jsonify({
            "jsonrpc": "2.0",
            "result": {
                "report": report
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
    app.run(host="127.0.0.1", port=8002, debug=True)