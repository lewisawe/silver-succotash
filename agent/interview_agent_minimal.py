from bedrock_agentcore.runtime import BedrockAgentCoreApp
import boto3
import json
import os
import re
from typing import Dict, Any

# Set region for us-east-1 (Nova Sonic compatibility)
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

app = BedrockAgentCoreApp()

# Direct Bedrock client instead of Strands
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

@app.entrypoint
def invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal interview agent with direct Nova Pro integration"""
    try:
        action = payload.get("action", "chat")
        
        handlers = {
            "generate_questions": generate_questions,
            "analyze_documents": analyze_documents,
            "process_response": process_response,
            "provide_feedback": provide_feedback,
            "chat": handle_chat
        }
        
        handler = handlers.get(action, handle_chat)
        return handler(payload)
        
    except Exception as e:
        return {"error": str(e), "success": False}

def call_nova_pro(prompt: str) -> str:
    """Direct Nova Pro call without Strands"""
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
        # Try direct JSON parse
        return json.loads(text.strip())
    except:
        pass
    
    # Try to find JSON in text
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

def generate_questions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate interview questions using Nova Pro"""
    role = payload.get("role", "Software Engineer")
    question_type = payload.get("question_type", "mixed")
    count = payload.get("count", 5)
    
    if question_type == "behavioral":
        focus = "behavioral questions using STAR method"
    elif question_type == "technical":
        focus = "technical questions about skills and problem-solving"
    else:
        focus = "mix of behavioral and technical questions"
    
    prompt = f"""Generate {count} interview questions for a {role} position. Focus on {focus}.

Return ONLY a JSON array in this exact format:
```json
[
    {{"question": "Tell me about a time you...", "type": "behavioral", "difficulty": "medium"}},
    {{"question": "How would you approach...", "type": "technical", "difficulty": "hard"}}
]
```"""
    
    response = call_nova_pro(prompt)
    
    # Parse response
    questions = parse_json_from_response(response, [
        {"question": f"Tell me about your experience as a {role}", "type": "behavioral", "difficulty": "medium"},
        {"question": f"What technical challenges have you faced in {role} work?", "type": "technical", "difficulty": "medium"},
        {"question": f"Describe a project you're proud of", "type": "behavioral", "difficulty": "easy"}
    ])
    
    # Ensure it's a list
    if not isinstance(questions, list):
        questions = [questions] if isinstance(questions, dict) else []
    
    return {
        "questions": questions[:count],
        "status": "success"
    }

def analyze_documents(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze CV against job description"""
    cv_content = payload.get("cv_content", "")
    job_description = payload.get("job_description", "")
    
    if not cv_content or not job_description:
        return {"error": "CV content and job description required", "success": False}
    
    prompt = f"""Analyze this candidate's CV against the job requirements:

CV: {cv_content[:1500]}

Job Description: {job_description[:1500]}

Provide analysis in this JSON format:
```json
{{
    "candidate_skills": ["skill1", "skill2"],
    "required_skills": ["skill1", "skill2"],
    "skill_matches": ["matched_skill"],
    "skill_gaps": ["missing_skill"],
    "experience_level": "junior|mid|senior",
    "strengths": ["strength1"],
    "recommendations": ["recommendation1"]
}}
```"""
    
    response = call_nova_pro(prompt)
    
    analysis = parse_json_from_response(response, {
        "candidate_skills": ["General programming"],
        "required_skills": ["Role-specific skills"],
        "skill_matches": ["Basic qualifications"],
        "skill_gaps": ["Advanced skills"],
        "experience_level": "mid",
        "strengths": ["Professional background"],
        "recommendations": ["Continue skill development"]
    })
    
    return {
        "analysis": analysis,
        "status": "success"
    }

def process_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process interview response and provide feedback"""
    user_response = payload.get("response", "")
    question = payload.get("question", "")
    
    if not user_response:
        return {"error": "Response required", "success": False}
    
    prompt = f"""Analyze this interview response:

Question: {question}
Response: {user_response}

Provide feedback in JSON format:
```json
{{
    "feedback": "Your response shows...",
    "score": 7,
    "strengths": ["clear communication"],
    "improvements": ["add more details"],
    "follow_up": "Can you elaborate?",
    "next_action": "continue"
}}
```

Score from 1-10. Be encouraging but constructive."""
    
    response = call_nova_pro(prompt)
    
    feedback = parse_json_from_response(response, {
        "feedback": "Thank you for your response.",
        "score": 6,
        "strengths": ["Answered the question"],
        "improvements": ["Provide more specific examples"],
        "follow_up": "Can you elaborate on that?",
        "next_action": "continue"
    })
    
    # Ensure score is valid
    if isinstance(feedback, dict) and "score" in feedback:
        try:
            feedback["score"] = max(1, min(10, int(feedback["score"])))
        except:
            feedback["score"] = 6
    
    return {
        "feedback": feedback,
        "status": "success"
    }

def provide_feedback(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive interview feedback"""
    responses = payload.get("responses", [])
    
    if not responses:
        return {"error": "No responses to analyze", "success": False}
    
    responses_text = "\n".join([
        f"Q: {r.get('question', '')}\nA: {r.get('response', '')}\nScore: {r.get('score', 'N/A')}"
        for r in responses
    ])
    
    prompt = f"""Analyze this complete interview session:

{responses_text}

Provide comprehensive feedback in JSON format:
```json
{{
    "overall_score": 75,
    "category_scores": {{
        "technical": 70,
        "communication": 80,
        "problem_solving": 75
    }},
    "strengths": ["clear communication"],
    "improvements": ["more technical depth"],
    "recommendations": ["practice system design"],
    "readiness": "ready|needs_practice|significant_improvement",
    "summary": "Overall strong performance."
}}
```"""
    
    response = call_nova_pro(prompt)
    
    feedback = parse_json_from_response(response, {
        "overall_score": 70,
        "category_scores": {"technical": 65, "communication": 75, "problem_solving": 70},
        "strengths": ["Professional demeanor"],
        "improvements": ["More specific examples"],
        "recommendations": ["Continue practicing"],
        "readiness": "needs_practice",
        "summary": "Good foundation with room for improvement."
    })
    
    return {
        "feedback": feedback,
        "status": "success"
    }

def handle_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle general chat"""
    message = payload.get("prompt", "Hello")
    
    prompt = f"""You are a helpful AI interview preparation assistant.
User: {message}
Provide a brief, encouraging response about interview preparation."""
    
    response = call_nova_pro(prompt)
    
    return {
        "result": {
            "content": [{"text": response}]
        },
        "status": "success"
    }

if __name__ == "__main__":
    app.run()
