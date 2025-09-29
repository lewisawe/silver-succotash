from typing import Dict, Any, Optional, List

def validate_document_analysis_payload(payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate document analysis request"""
    cv_content = payload.get("cv_content", "")
    job_description = payload.get("job_description", "")
    
    if not cv_content or not cv_content.strip():
        return False, "CV content is required"
    
    if not job_description or not job_description.strip():
        return False, "Job description is required"
    
    if len(cv_content) < 50:
        return False, "CV content too short (minimum 50 characters)"
    
    if len(job_description) < 30:
        return False, "Job description too short (minimum 30 characters)"
    
    return True, None

def validate_question_generation_payload(payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate question generation request"""
    role = payload.get("role", "")
    question_type = payload.get("question_type", "mixed")
    count = payload.get("count", 5)
    
    if not role or not role.strip():
        return False, "Role is required"
    
    valid_types = ["behavioral", "technical", "mixed"]
    if question_type not in valid_types:
        return False, f"Question type must be one of: {valid_types}"
    
    try:
        count = int(count)
        if count < 1 or count > 20:
            return False, "Question count must be between 1 and 20"
    except (ValueError, TypeError):
        return False, "Question count must be a valid number"
    
    return True, None

def validate_response_processing_payload(payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate response processing request"""
    user_response = payload.get("response", "")
    question = payload.get("question", "")
    
    if not user_response or not user_response.strip():
        return False, "User response is required"
    
    if not question or not question.strip():
        return False, "Question is required"
    
    if len(user_response.strip()) < 10:
        return False, "Response too short (minimum 10 characters)"
    
    return True, None

def validate_feedback_generation_payload(payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate feedback generation request"""
    responses = payload.get("responses", [])
    
    if not isinstance(responses, list):
        return False, "Responses must be a list"
    
    if len(responses) == 0:
        return False, "At least one response is required for feedback"
    
    for i, response in enumerate(responses):
        if not isinstance(response, dict):
            return False, f"Response {i+1} must be an object"
        
        if not response.get("question"):
            return False, f"Response {i+1} missing question"
        
        if not response.get("response"):
            return False, f"Response {i+1} missing user response"
    
    return True, None

def sanitize_text_input(text: str, max_length: int = 5000) -> str:
    """Sanitize text input"""
    if not isinstance(text, str):
        return ""
    
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize entire payload"""
    sanitized = {}
    
    for key, value in payload.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text_input(value)
        elif isinstance(value, (int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = value[:100]  # Limit list size
        elif isinstance(value, dict):
            sanitized[key] = {k: v for k, v in value.items() if k in ['question', 'response', 'score', 'type', 'difficulty']}
        else:
            sanitized[key] = str(value)
    
    return sanitized
