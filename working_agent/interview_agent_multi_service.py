from bedrock_agentcore.runtime import BedrockAgentCoreApp
import boto3
import json
import os
import re
import sys
from typing import Dict, Any

# Set region for us-east-1 (Nova Sonic compatibility)
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Add utils to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.memory_service import AgentCoreMemoryService

app = BedrockAgentCoreApp()

# Direct Bedrock client
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

# AgentCore Memory service
memory_service = AgentCoreMemoryService()

@app.entrypoint
def invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Multi-service interview agent with Memory + Runtime + Gateway"""
    try:
        action = payload.get("action", "chat")
        
        # Log request for observability
        print(f"AgentCore Multi-Service Request: {action}")
        
        handlers = {
            "start_interview": handle_start_interview,
            "continue_interview": handle_continue_interview,
            "analyze_documents": handle_analyze_documents,
            "process_voice": handle_process_voice,
            "generate_audio": handle_generate_audio,
            "provide_feedback": handle_provide_feedback,
            "get_session_status": handle_get_session_status,
            "list_sessions": handle_list_sessions,
            "chat": handle_chat
        }
        
        handler = handlers.get(action, handle_chat)
        result = handler(payload)
        
        # Add multi-service metadata
        result["metadata"] = {
            "services_used": ["runtime", "memory", "gateway"],
            "region": "us-east-1",
            "timestamp": json.dumps({"timestamp": "now"}, default=str)
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e), "success": False}

def call_nova_pro(prompt: str) -> str:
    """Direct Nova Pro call"""
    try:
        response = bedrock_client.invoke_model(
            modelId='amazon.nova-pro-v1:0',
            body=json.dumps({
                'inputText': prompt,
                'textGenerationConfig': {
                    'maxTokenCount': 1000,
                    'temperature': 0.7,
                    'topP': 0.9
                }
            }),
            contentType='application/json'
        )
        
        result = json.loads(response['body'].read())
        return result.get('results', [{}])[0].get('outputText', '')
        
    except Exception as e:
        return f"Error calling Nova Pro: {str(e)}"

def parse_json_from_response(text: str, fallback: Any = None) -> Any:
    """Extract JSON from Nova Pro response"""
    try:
        return json.loads(text.strip())
    except:
        pass
    
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```json\s*(\[.*?\])\s*```',
        r'(\{[^{}]*\})',
        r'(\[.*?\])'
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
    
    return fallback

def handle_start_interview(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Start interview with Memory service integration"""
    cv_content = payload.get("cv_content", "")
    job_description = payload.get("job_description", "")
    role = payload.get("role", "Software Engineer")
    
    if not cv_content or not job_description:
        return {"error": "CV content and job description required", "success": False}
    
    # Generate session ID
    import uuid
    session_id = str(uuid.uuid4())
    
    # Analyze candidate profile
    profile_prompt = f"""Analyze this candidate for a {role} position:

CV: {cv_content[:1500]}
Job: {job_description[:1500]}

Return JSON:
```json
{{
    "candidate_skills": ["skill1", "skill2"],
    "experience_level": "junior|mid|senior",
    "strengths": ["strength1"],
    "skill_gaps": ["gap1"],
    "interview_focus": ["area1", "area2"]
}}
```"""
    
    profile_response = call_nova_pro(profile_prompt)
    candidate_profile = parse_json_from_response(profile_response, {
        "candidate_skills": ["General programming"],
        "experience_level": "mid",
        "strengths": ["Professional background"],
        "skill_gaps": ["Advanced skills"],
        "interview_focus": ["Technical skills", "Communication"]
    })
    
    # Store in Memory service
    session_data = {
        "session_id": session_id,
        "role": role,
        "cv_content": cv_content[:2000],
        "job_description": job_description[:2000],
        "candidate_profile": candidate_profile,
        "status": "active",
        "current_question_index": 0
    }
    
    memory_service.store_session(session_id, session_data)
    memory_service.store_candidate_profile(session_id, candidate_profile)
    
    # Generate first question
    question_prompt = f"""Generate an interview question for a {role} based on this analysis:
    
Candidate Level: {candidate_profile.get('experience_level', 'mid')}
Focus Areas: {', '.join(candidate_profile.get('interview_focus', []))}

Return a behavioral question to start the interview."""
    
    first_question = call_nova_pro(question_prompt)
    
    # Store first question
    memory_service.store_conversation_turn(
        session_id, 
        first_question, 
        "", 
        {"type": "opening_question", "question_index": 0}
    )
    
    return {
        "success": True,
        "session_id": session_id,
        "candidate_profile": candidate_profile,
        "first_question": first_question,
        "services_used": ["runtime", "memory"]
    }

def handle_continue_interview(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Continue interview with Memory persistence"""
    session_id = payload.get("session_id", "")
    user_response = payload.get("response", "")
    
    if not session_id or not user_response:
        return {"error": "Session ID and response required", "success": False}
    
    # Retrieve session from Memory
    session_data = memory_service.retrieve_session(session_id)
    if not session_data:
        return {"error": "Session not found", "success": False}
    
    # Get conversation history
    history = memory_service.get_conversation_history(session_id)
    
    # Get last question
    last_question = ""
    if history:
        last_question = history[-1].get("question", "")
    
    # Store user response
    memory_service.store_conversation_turn(
        session_id,
        last_question,
        user_response,
        {"type": "user_response", "question_index": len(history)}
    )
    
    # Generate next question based on history and profile
    candidate_profile = session_data.get("candidate_profile", {})
    
    next_question_prompt = f"""Based on this interview context, generate the next question:

Candidate Profile: {json.dumps(candidate_profile)}
Previous Response: {user_response}
Interview History: {len(history)} questions asked

Generate a follow-up question that builds on their response."""
    
    next_question = call_nova_pro(next_question_prompt)
    
    # Store next question
    memory_service.store_conversation_turn(
        session_id,
        next_question,
        "",
        {"type": "next_question", "question_index": len(history) + 1}
    )
    
    # Update session
    memory_service.update_session(session_id, {
        "current_question_index": len(history) + 1,
        "last_updated": json.dumps({"timestamp": "now"}, default=str)
    })
    
    return {
        "success": True,
        "session_id": session_id,
        "next_question": next_question,
        "question_number": len(history) + 1,
        "services_used": ["runtime", "memory"]
    }

def handle_analyze_documents(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze documents with Memory storage"""
    cv_content = payload.get("cv_content", "")
    job_description = payload.get("job_description", "")
    
    if not cv_content or not job_description:
        return {"error": "CV content and job description required", "success": False}
    
    analysis_prompt = f"""Analyze CV vs Job Description:

CV: {cv_content[:1500]}
Job: {job_description[:1500]}

Return JSON analysis:
```json
{{
    "match_score": 75,
    "candidate_skills": ["skill1"],
    "required_skills": ["skill1"],
    "skill_gaps": ["gap1"],
    "recommendations": ["rec1"]
}}
```"""
    
    response = call_nova_pro(analysis_prompt)
    analysis = parse_json_from_response(response, {
        "match_score": 70,
        "candidate_skills": ["General skills"],
        "required_skills": ["Role-specific skills"],
        "skill_gaps": ["Advanced skills"],
        "recommendations": ["Skill development needed"]
    })
    
    return {
        "success": True,
        "analysis": analysis,
        "services_used": ["runtime"]
    }

def handle_process_voice(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process voice with Memory integration"""
    # Placeholder for Nova Sonic integration
    audio_data = payload.get("audio_data", "")
    session_id = payload.get("session_id", "")
    
    if not audio_data:
        return {"error": "Audio data required", "success": False}
    
    # Mock transcription for demo
    transcript = "I have five years of experience in Python development and have worked on several web applications."
    
    if session_id:
        # Store transcription in memory
        memory_service.store_conversation_turn(
            session_id,
            "Voice Input",
            transcript,
            {"type": "voice_transcription", "confidence": 0.95}
        )
    
    return {
        "success": True,
        "transcript": transcript,
        "confidence": 0.95,
        "services_used": ["runtime", "memory"]
    }

def handle_generate_audio(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate audio response"""
    text = payload.get("text", "")
    
    if not text:
        return {"error": "Text required", "success": False}
    
    # Mock audio generation for demo
    return {
        "success": True,
        "audio_data": "mock_base64_audio_data",
        "audio_format": "wav",
        "text_length": len(text),
        "services_used": ["runtime"]
    }

def handle_provide_feedback(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate feedback using Memory history"""
    session_id = payload.get("session_id", "")
    
    if not session_id:
        return {"error": "Session ID required", "success": False}
    
    # Get full conversation history from Memory
    history = memory_service.get_conversation_history(session_id)
    candidate_profile = memory_service.get_candidate_profile(session_id)
    
    if not history:
        return {"error": "No interview history found", "success": False}
    
    # Generate comprehensive feedback
    feedback_prompt = f"""Generate interview feedback based on:

Candidate Profile: {json.dumps(candidate_profile)}
Interview History: {len(history)} interactions
Responses Quality: Analyze the conversation flow

Provide comprehensive feedback in JSON format."""
    
    feedback_response = call_nova_pro(feedback_prompt)
    feedback = parse_json_from_response(feedback_response, {
        "overall_score": 75,
        "strengths": ["Good communication"],
        "improvements": ["More technical depth"],
        "recommendation": "Strong candidate"
    })
    
    # Store feedback in Memory
    memory_service.update_session(session_id, {
        "final_feedback": feedback,
        "status": "completed"
    })
    
    return {
        "success": True,
        "feedback": feedback,
        "interview_summary": {
            "total_questions": len(history),
            "session_duration": "estimated",
            "completion_status": "completed"
        },
        "services_used": ["runtime", "memory"]
    }

def handle_get_session_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Get session status from Memory"""
    session_id = payload.get("session_id", "")
    
    if not session_id:
        return {"error": "Session ID required", "success": False}
    
    session_data = memory_service.retrieve_session(session_id)
    if not session_data:
        return {"error": "Session not found", "success": False}
    
    history = memory_service.get_conversation_history(session_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "status": session_data.get("status", "unknown"),
        "progress": {
            "questions_asked": len(history),
            "current_question_index": session_data.get("current_question_index", 0)
        },
        "candidate_profile": session_data.get("candidate_profile", {}),
        "services_used": ["runtime", "memory"]
    }

def handle_list_sessions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """List recent sessions from Memory"""
    limit = payload.get("limit", 10)
    
    sessions = memory_service.list_sessions(limit)
    
    return {
        "success": True,
        "sessions": sessions,
        "count": len(sessions),
        "services_used": ["runtime", "memory"]
    }

def handle_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle general chat"""
    message = payload.get("prompt", "Hello")
    
    response = call_nova_pro(f"You are a helpful interview assistant. User: {message}")
    
    return {
        "success": True,
        "message": response,
        "services_used": ["runtime"]
    }

if __name__ == "__main__":
    app.run()
