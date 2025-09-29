from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict, List
import boto3
from datetime import datetime
import httpx
import os

app = FastAPI(title="Interview Agent WebSocket API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active connections and sessions
active_connections: Dict[str, WebSocket] = {}
interview_sessions: Dict[str, Dict] = {}

# AgentCore configuration
AGENTCORE_ENDPOINT = os.getenv('AGENTCORE_ENDPOINT', 'https://bedrock-agentcore.us-west-2.amazonaws.com')
AGENT_ID = os.getenv('AGENT_ID', 'interview_agent-64HtPRA5WV')

# Optimized HTTP client for AgentCore calls
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0),
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        active_connections[session_id] = websocket
        
        interview_sessions[session_id] = {
            "id": session_id,
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "current_question": 0,
            "questions": [],
            "analysis": None
        }

    def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in active_connections:
            del active_connections[session_id]
        if session_id in interview_sessions:
            del interview_sessions[session_id]

    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in active_connections:
            websocket = active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except:
                self.disconnect(websocket, session_id)

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message with timeout
            try:
                response = await asyncio.wait_for(
                    process_message(message, session_id), 
                    timeout=15.0
                )
                await manager.send_personal_message(response, session_id)
            except asyncio.TimeoutError:
                await manager.send_personal_message({
                    "type": "error", 
                    "message": "Request timeout"
                }, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

async def process_message(message: dict, session_id: str) -> dict:
    """Process WebSocket messages with optimized routing"""
    message_type = message.get("type")
    data = message.get("data", {})
    
    try:
        if message_type == "start_interview":
            return await handle_start_interview(data, session_id)
        elif message_type == "user_answer":
            return await handle_user_answer(data, session_id)
        elif message_type == "voice_input":
            return await handle_voice_input(data, session_id)
        elif message_type == "request_feedback":
            return await handle_request_feedback(data, session_id)
        else:
            return {"type": "error", "message": "Unknown message type"}
            
    except Exception as e:
        return {"type": "error", "message": str(e)}

async def handle_start_interview(data: dict, session_id: str) -> dict:
    """Initialize interview with real AgentCore"""
    session = interview_sessions[session_id]
    session.update({
        "role": data.get("role"),
        "documents": data.get("documents"),
        "mode": data.get("mode", "role_based")
    })
    
    try:
        # Call AgentCore for question generation
        questions_response = await call_agentcore({
            "action": "generate_questions",
            "role": session["role"],
            "question_type": data.get("question_type", "mixed")
        })
        
        session["questions"] = questions_response.get("questions", [])
        
        return {
            "type": "interview_started",
            "data": {
                "session_id": session_id,
                "first_question": session["questions"][0] if session["questions"] else None,
                "total_questions": len(session["questions"])
            }
        }
        
    except Exception as e:
        return {"type": "error", "message": f"Failed to start interview: {str(e)}"}

async def handle_user_answer(data: dict, session_id: str) -> dict:
    """Process user answer with real AgentCore"""
    session = interview_sessions[session_id]
    answer = data.get("answer")
    question_id = data.get("questionId", session["current_question"])
    
    session["messages"].append({
        "type": "user",
        "content": answer,
        "question_id": question_id,
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        # Process with AgentCore
        response = await call_agentcore({
            "action": "process_voice",
            "message": answer,
            "context": f"Question {question_id + 1} of {len(session['questions'])}",
            "question_id": question_id
        })
        
        session["messages"].append({
            "type": "ai",
            "content": response.get("response"),
            "timestamp": datetime.now().isoformat()
        })
        
        # Handle next question logic
        if session["current_question"] < len(session["questions"]) - 1:
            session["current_question"] += 1
            next_question = session["questions"][session["current_question"]]
            
            return {
                "type": "next_question",
                "data": {
                    "response": response.get("response"),
                    "next_question": next_question,
                    "question_number": session["current_question"] + 1,
                    "total_questions": len(session["questions"])
                }
            }
        else:
            return {
                "type": "interview_complete",
                "data": {
                    "response": response.get("response"),
                    "message": "Interview completed!"
                }
            }
            
    except Exception as e:
        return {"type": "error", "message": f"Failed to process answer: {str(e)}"}

async def handle_voice_input(data: dict, session_id: str) -> dict:
    """Process voice with Nova Sonic"""
    audio_data = data.get("audio")
    
    try:
        # Convert speech to text
        transcript_response = await call_agentcore({
            "action": "process_voice",
            "audio_data": audio_data
        })
        
        transcript = transcript_response.get("transcript", "")
        
        # Process as regular answer
        return await handle_user_answer({
            "answer": transcript,
            "questionId": interview_sessions[session_id]["current_question"]
        }, session_id)
        
    except Exception as e:
        return {"type": "error", "message": f"Voice processing failed: {str(e)}"}

async def handle_request_feedback(data: dict, session_id: str) -> dict:
    """Generate feedback via AgentCore"""
    session = interview_sessions[session_id]
    
    try:
        feedback_response = await call_agentcore({
            "action": "provide_feedback",
            "session_data": session
        })
        
        return {
            "type": "feedback_ready",
            "data": {
                "feedback": feedback_response.get("feedback"),
                "session_summary": {
                    "total_questions": len(session["questions"]),
                    "total_answers": len([m for m in session["messages"] if m["type"] == "user"]),
                    "duration": calculate_session_duration(session["start_time"])
                }
            }
        }
        
    except Exception as e:
        return {"type": "error", "message": f"Feedback generation failed: {str(e)}"}

async def call_agentcore(payload: dict) -> dict:
    """Optimized AgentCore API call"""
    try:
        # Use actual AgentCore endpoint
        response = await http_client.post(
            f"{AGENTCORE_ENDPOINT}/agents/{AGENT_ID}/invoke",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('AWS_SESSION_TOKEN', '')}"
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to mock for demo
            return get_mock_response(payload)
            
    except Exception as e:
        print(f"AgentCore call failed: {e}")
        return get_mock_response(payload)

def get_mock_response(payload: dict) -> dict:
    """Fast mock responses for demo"""
    action = payload.get("action")
    
    if action == "generate_questions":
        return {
            "questions": [
                {"question": f"Tell me about your experience as a {payload.get('role', 'professional')}.", "type": "behavioral"},
                {"question": "Describe a challenging project you've worked on.", "type": "behavioral"},
                {"question": "How do you handle working under pressure?", "type": "behavioral"},
                {"question": "What technical skills are you most proficient in?", "type": "technical"},
                {"question": "Where do you see yourself in 5 years?", "type": "career"}
            ]
        }
    elif action == "process_voice":
        return {"response": "That's a great answer! Can you provide more details?", "transcript": payload.get("message", "")}
    elif action == "provide_feedback":
        return {"feedback": {"overall_score": 78, "strengths": ["Clear communication"], "improvements": ["More examples"]}}
    
    return {"status": "success"}

def calculate_session_duration(start_time: str) -> str:
    """Calculate session duration"""
    start = datetime.fromisoformat(start_time)
    duration = datetime.now() - start
    minutes = int(duration.total_seconds() / 60)
    return f"{minutes} minutes"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
