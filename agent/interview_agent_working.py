from bedrock_agentcore.runtime import BedrockAgentCoreApp
import json
import os

# Minimal working agent for hackathon demo
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """Minimal multi-service interview agent"""
    try:
        action = payload.get("action", "chat")
        
        # Mock responses for demo
        if action == "start_interview":
            return {
                "success": True,
                "session_id": "demo-session-123",
                "candidate_profile": {
                    "experience_level": "mid",
                    "candidate_skills": ["Python", "JavaScript"],
                    "strengths": ["Problem solving", "Communication"],
                    "interview_focus": ["Technical skills", "Leadership"]
                },
                "first_question": "Tell me about your experience with Python development and how you've used it in recent projects.",
                "services_used": ["runtime", "memory", "gateway"]
            }
            
        elif action == "continue_interview":
            return {
                "success": True,
                "next_question": "How do you approach debugging complex issues in production systems?",
                "question_number": 2,
                "services_used": ["runtime", "memory"]
            }
            
        elif action == "analyze_documents":
            return {
                "success": True,
                "analysis": {
                    "match_score": 85,
                    "candidate_skills": ["Python", "AWS", "React"],
                    "required_skills": ["Python", "AWS", "Leadership"],
                    "skill_gaps": ["Leadership experience"],
                    "recommendations": ["Highlight leadership examples"]
                },
                "services_used": ["runtime"]
            }
            
        elif action == "provide_feedback":
            return {
                "success": True,
                "feedback": {
                    "overall_score": 82,
                    "strengths": ["Strong technical knowledge", "Clear communication"],
                    "improvements": ["More specific examples", "Leadership stories"],
                    "readiness": "ready",
                    "summary": "Strong candidate with good technical foundation and communication skills."
                },
                "interview_summary": {
                    "total_questions": 5,
                    "completion_status": "completed"
                },
                "services_used": ["runtime", "memory"]
            }
            
        elif action == "process_voice":
            return {
                "success": True,
                "transcript": "I have been working with Python for over 5 years, primarily in web development and data analysis projects.",
                "confidence": 0.95,
                "services_used": ["runtime", "memory"]
            }
            
        elif action == "get_session_status":
            return {
                "success": True,
                "session_id": payload.get("session_id", "demo-session-123"),
                "status": "active",
                "progress": {
                    "questions_asked": 3,
                    "current_question_index": 3
                },
                "services_used": ["runtime", "memory"]
            }
            
        else:  # chat or default
            return {
                "success": True,
                "message": "Hello! I'm your AI interview assistant powered by AgentCore Runtime, Memory, and Gateway services. I can help you practice interviews with personalized questions and feedback.",
                "services_used": ["runtime"]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    app.run()
