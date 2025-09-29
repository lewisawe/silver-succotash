import json
import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

app = FastAPI(title="AgentCore Bridge Server")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AWS Bedrock AgentCore client with timeout configuration
bedrock_client = boto3.client(
    'bedrock-agentcore', 
    region_name='us-west-2',
    config=boto3.session.Config(
        read_timeout=60,  # 60 second timeout
        retries={'max_attempts': 2}
    )
)

# AgentCore Runtime ARN
AGENT_ARN = "arn:aws:bedrock-agentcore:us-west-2:120651511769:runtime/interview_agent-64HtPRA5WV"

class QuestionRequest(BaseModel):
    role: str
    cv: str = ""
    jobDescription: str = ""
    additionalContext: str = ""
    questionType: str = "mixed"  # behavioral, technical, or mixed

def call_agentcore_sync(payload):
    """Synchronous AgentCore call for timeout handling"""
    try:
        response = bedrock_client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_ARN,
            contentType='application/json',
            accept='application/json',
            payload=json.dumps(payload)
        )
        
        response_body = response['response'].read()
        response_data = json.loads(response_body.decode('utf-8'))
        return response_data
    except Exception as e:
        print(f"AgentCore call error: {e}")
        raise e

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agentcore-proxy"}

@app.post("/generate-questions")
async def generate_questions(request: QuestionRequest):
    """Generate interview questions using AgentCore SDK with timeout"""
    try:
        # Prepare payload for AgentCore
        payload = {
            "action": "generate_questions",
            "role": request.role,
            "cv": request.cv,
            "job_description": request.jobDescription,
            "additional_context": request.additionalContext,
            "question_type": request.questionType
        }
        
        print(f"Calling AgentCore for role: {request.role}")
        
        # Call AgentCore with timeout using thread executor
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_event_loop()
        
        try:
            # 45 second timeout for AgentCore call
            response_data = await asyncio.wait_for(
                loop.run_in_executor(executor, call_agentcore_sync, payload),
                timeout=45.0
            )
            
            # Extract questions from response
            questions = response_data.get("questions", [])
            print(f"AgentCore returned {len(questions)} questions")
            
            return {"questions": questions}
            
        except asyncio.TimeoutError:
            print("AgentCore call timed out, using fallback questions")
            # Fallback questions when AgentCore times out
            fallback_questions = [
                {
                    "question": f"Tell me about your background and experience relevant to this {request.role} position.",
                    "type": "behavioral",
                    "difficulty": "easy",
                    "focus_area": "experience",
                    "expected_points": ["Relevant experience", "Career progression", "Skills alignment"]
                },
                {
                    "question": f"Describe a challenging situation you faced in your {request.role.lower()} work and how you handled it.",
                    "type": "behavioral",
                    "difficulty": "medium",
                    "focus_area": "problem_solving",
                    "expected_points": ["Problem identification", "Solution approach", "Results achieved"]
                },
                {
                    "question": f"What technical skills and methodologies do you use in your {request.role.lower()} work?",
                    "type": "technical",
                    "difficulty": "medium",
                    "focus_area": "technical_skills",
                    "expected_points": ["Technical knowledge", "Best practices", "Continuous learning"]
                }
            ]
            return {"questions": fallback_questions, "status": "fallback", "reason": "timeout"}
            
    except Exception as e:
        print(f"AgentCore SDK error: {str(e)}")
        # Return fallback questions on any error
        fallback_questions = [
            {
                "question": f"What interests you most about working as a {request.role}?",
                "type": "behavioral",
                "difficulty": "easy",
                "focus_area": "motivation",
                "expected_points": ["Career motivation", "Industry interest", "Role alignment"]
            },
            {
                "question": f"How do you stay updated with trends and developments in the {request.role.lower()} field?",
                "type": "behavioral",
                "difficulty": "easy",
                "focus_area": "continuous_learning",
                "expected_points": ["Learning resources", "Professional development", "Industry engagement"]
            }
        ]
        return {"questions": fallback_questions, "status": "error", "reason": str(e)}

def signal_handler(sig, frame):
    print('\\n🛑 Shutting down bridge server...')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("🌉 Starting AgentCore Bridge Server with timeout handling...")
    print("🔗 AgentCore ARN:", AGENT_ARN)
    print("⏱️  Timeout: 45 seconds with fallback questions")
    uvicorn.run(app, host="0.0.0.0", port=8081)
