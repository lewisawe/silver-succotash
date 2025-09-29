import json
import re
from typing import Any, Dict, List, Optional

def parse_json_response(text: str, fallback_data: Any = None) -> Any:
    """
    Robust JSON parsing from LLM responses with multiple fallback strategies
    """
    if not text:
        return fallback_data
    
    # Strategy 1: Try direct JSON parsing
    try:
        return json.loads(text.strip())
    except:
        pass
    
    # Strategy 2: Extract from code blocks
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',      # JSON code blocks
        r'```json\s*(\[.*?\])\s*```',      # JSON arrays in code blocks
        r'```\s*(\{.*?\})\s*```',          # Generic code blocks with objects
        r'```\s*(\[.*?\])\s*```',          # Generic code blocks with arrays
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
    
    # Strategy 3: Find JSON-like structures
    simple_patterns = [
        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',  # Nested objects
        r'(\[.*?\])',                           # Arrays
    ]
    
    for pattern in simple_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
    
    # Strategy 4: Extract key-value pairs manually
    if isinstance(fallback_data, dict):
        extracted = extract_key_values(text, fallback_data.keys())
        if extracted:
            return {**fallback_data, **extracted}
    
    return fallback_data

def extract_key_values(text: str, keys: List[str]) -> Dict[str, Any]:
    """
    Extract key-value pairs from text when JSON parsing fails
    """
    extracted = {}
    
    for key in keys:
        # Look for key: value patterns
        patterns = [
            rf'"{key}":\s*"([^"]*)"',           # "key": "value"
            rf'"{key}":\s*(\d+)',               # "key": 123
            rf'"{key}":\s*\[(.*?)\]',           # "key": [array]
            rf'{key}:\s*"([^"]*)"',             # key: "value"
            rf'{key}:\s*(\d+)',                 # key: 123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1)
                # Try to parse as number
                try:
                    extracted[key] = int(value)
                except:
                    try:
                        extracted[key] = float(value)
                    except:
                        extracted[key] = value
                break
    
    return extracted

def validate_question_format(questions: Any) -> List[Dict[str, str]]:
    """
    Validate and clean question format
    """
    if not isinstance(questions, list):
        return []
    
    validated = []
    for q in questions:
        if isinstance(q, dict) and 'question' in q:
            validated.append({
                'question': str(q.get('question', '')),
                'type': str(q.get('type', 'general')),
                'difficulty': str(q.get('difficulty', 'medium'))
            })
        elif isinstance(q, str):
            validated.append({
                'question': q,
                'type': 'general',
                'difficulty': 'medium'
            })
    
    return validated

def validate_feedback_format(feedback: Any) -> Dict[str, Any]:
    """
    Validate and clean feedback format
    """
    if not isinstance(feedback, dict):
        return {
            "feedback": "Unable to process feedback",
            "score": 5,
            "strengths": [],
            "improvements": [],
            "follow_up": "",
            "next_action": "continue"
        }
    
    return {
        "feedback": str(feedback.get("feedback", "")),
        "score": max(1, min(10, int(feedback.get("score", 5)))),
        "strengths": feedback.get("strengths", []) if isinstance(feedback.get("strengths"), list) else [],
        "improvements": feedback.get("improvements", []) if isinstance(feedback.get("improvements"), list) else [],
        "follow_up": str(feedback.get("follow_up", "")),
        "next_action": str(feedback.get("next_action", "continue"))
    }
