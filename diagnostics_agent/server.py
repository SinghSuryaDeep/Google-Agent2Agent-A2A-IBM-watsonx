"""
Author: SURYA DEEP SINGH
LinkedIn: https://www.linkedin.com/in/surya-deep-singh-b9b94813a/
"""

#Server.py  
import asyncio
import logging
import json
from flask import Flask, jsonify, request
from diagnostics_logic import analyze_patient_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# A2A Compliant Agent Card
agent_card = {
    "apiVersion": "a2a/v0.2",  # A2A protocol version
    "kind": "AgentCard",
    "metadata": {
        "id": "diagnostics-agent",
        "name": "DiagnosticsAgent", 
        "description": "Analyzes patient symptoms and vitals to return a probable diagnosis.",
        "version": "1.0.0",
        "tags": ["healthcare", "diagnosis", "medical"]
    },
    "spec": {
        "url": "http://127.0.0.1:8001",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "interactionModes": ["synchronous"]
        },
        "authentication": {
            "schemes": ["none"]  # A2A supports various auth schemes
        },
        "skills": [
            {
                "id": "analyze-patient-data",
                "name": "Analyze Patient Data",
                "description": "Analyze symptoms & vitals to derive a medical diagnosis",
                "tags": ["diagnosis", "healthcare", "medical-analysis"],
                "examples": [
                    {
                        "description": "Analyze patient with respiratory symptoms",
                        "input": {
                            "patient_data": {
                                "symptoms": ["persistent cough", "fever", "shortness of breath"],
                                "vitals": {"temperature": "101.5 F", "pulse": "110 bpm", "spo2": "94%"}
                            }
                        },
                        "output": {
                            "diagnosis": {
                                "condition": "Possible respiratory infection",
                                "risk": "Medium"
                            }
                        }
                    }
                ],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_data": {
                            "type": "object",
                            "properties": {
                                "symptoms": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of patient symptoms"
                                },
                                "vitals": {
                                    "type": "object",
                                    "description": "Patient vital signs"
                                }
                            },
                            "required": ["symptoms"]
                        }
                    },
                    "required": ["patient_data"]
                },
                "outputSchema": {
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
                "invocation": {
                    "method": "POST",
                    "endpoint": "/skills/analyze-patient-data",
                    "contentType": "application/json"
                }
            }
        ]
    }
}

# A2A Protocol Endpoints

@app.route("/.well-known/agent.json", methods=["GET"])
def agent_manifest():
    """A2A Agent Discovery Endpoint"""
    return jsonify(agent_card)

@app.route("/skills/analyze-patient-data", methods=["POST"])
def analyze_skill():
    """A2A Compliant Skill Invocation"""
    try:
        # A2A uses JSON-RPC 2.0 format for requests
        request_data = request.json
        
        # Validate JSON-RPC 2.0 structure
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
        patient_data = params.get("patient_data")
        
        if not patient_data:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params - Missing 'patient_data'"
                },
                "id": request_data["id"]
            }), 400
        
        # Perform analysis
        result = analyze_patient_data(patient_data)
        
        # A2A JSON-RPC 2.0 Response
        return jsonify({
            "jsonrpc": "2.0",
            "result": {
                "diagnosis": result
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

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "protocol": "A2A v0.2"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=True)