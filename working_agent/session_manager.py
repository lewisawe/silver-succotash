import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class InterviewSession:
    """Manages interview session state and autonomous flow"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.state = "initialized"  # initialized, analyzing, questioning, completed
        self.current_question_index = 0
        self.questions = []
        self.responses = []
        self.candidate_analysis = {}
        self.interview_config = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "state": self.state,
            "current_question_index": self.current_question_index,
            "questions": self.questions,
            "responses": self.responses,
            "candidate_analysis": self.candidate_analysis,
            "interview_config": self.interview_config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterviewSession':
        """Create session from dictionary"""
        session = cls(data.get("session_id"))
        session.created_at = data.get("created_at", datetime.now().isoformat())
        session.state = data.get("state", "initialized")
        session.current_question_index = data.get("current_question_index", 0)
        session.questions = data.get("questions", [])
        session.responses = data.get("responses", [])
        session.candidate_analysis = data.get("candidate_analysis", {})
        session.interview_config = data.get("interview_config", {})
        return session

class AutonomousInterviewFlow:
    """Manages autonomous interview progression"""
    
    def __init__(self):
        self.sessions = {}  # In-memory storage for now
    
    def start_interview(self, cv_content: str, job_description: str, role: str) -> Dict[str, Any]:
        """Start new interview session"""
        session = InterviewSession()
        session.state = "analyzing"
        session.interview_config = {
            "role": role,
            "cv_content": cv_content[:2000],
            "job_description": job_description[:2000],
            "difficulty_level": "medium",
            "question_types": ["behavioral", "technical", "situational"]
        }
        
        self.sessions[session.session_id] = session
        
        return {
            "session_id": session.session_id,
            "state": "analyzing",
            "message": "Interview session started. Analyzing your background...",
            "next_action": "analyze_candidate"
        }
    
    def process_analysis(self, session_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Process candidate analysis and generate questions"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        session.candidate_analysis = analysis
        session.state = "questioning"
        
        # Generate initial questions based on analysis
        questions = self._generate_adaptive_questions(session)
        session.questions = questions
        
        return {
            "session_id": session_id,
            "state": "questioning",
            "current_question": questions[0] if questions else None,
            "question_number": 1,
            "total_questions": len(questions),
            "message": "Analysis complete. Let's begin the interview!"
        }
    
    def process_response(self, session_id: str, response: str) -> Dict[str, Any]:
        """Process user response and determine next action"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        current_question = session.questions[session.current_question_index]
        
        # Store response
        response_data = {
            "question": current_question["question"],
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "question_type": current_question.get("type", "general")
        }
        session.responses.append(response_data)
        
        # Determine next action
        next_action = self._determine_next_action(session, response)
        
        if next_action == "next_question":
            session.current_question_index += 1
            if session.current_question_index >= len(session.questions):
                session.state = "completed"
                return {
                    "session_id": session_id,
                    "state": "completed",
                    "message": "Interview completed! Generating final feedback...",
                    "next_action": "generate_feedback"
                }
            else:
                next_question = session.questions[session.current_question_index]
                return {
                    "session_id": session_id,
                    "state": "questioning",
                    "current_question": next_question,
                    "question_number": session.current_question_index + 1,
                    "total_questions": len(session.questions),
                    "message": "Great answer! Let's continue.",
                    "next_action": "continue"
                }
        
        elif next_action == "follow_up":
            follow_up = self._generate_follow_up(session, response)
            return {
                "session_id": session_id,
                "state": "questioning",
                "current_question": {"question": follow_up, "type": "follow_up"},
                "question_number": session.current_question_index + 1,
                "total_questions": len(session.questions),
                "message": "I'd like to dig deeper into that...",
                "next_action": "continue"
            }
        
        elif next_action == "adjust_difficulty":
            # Add harder/easier questions based on performance
            new_questions = self._adjust_question_difficulty(session)
            session.questions.extend(new_questions)
            return {
                "session_id": session_id,
                "state": "questioning", 
                "message": "Adjusting interview based on your responses...",
                "next_action": "continue"
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "state": session.state,
            "progress": {
                "current_question": session.current_question_index + 1,
                "total_questions": len(session.questions),
                "completed_responses": len(session.responses)
            },
            "candidate_analysis": session.candidate_analysis
        }
    
    def _generate_adaptive_questions(self, session: InterviewSession) -> List[Dict[str, Any]]:
        """Generate questions based on candidate analysis"""
        analysis = session.candidate_analysis
        role = session.interview_config.get("role", "")
        
        questions = []
        
        # Start with behavioral questions
        questions.extend([
            {"question": f"Tell me about your experience as a {role}", "type": "behavioral", "difficulty": "easy"},
            {"question": "Describe a challenging project you worked on recently", "type": "behavioral", "difficulty": "medium"}
        ])
        
        # Add technical questions based on skill gaps
        skill_gaps = analysis.get("skill_gaps", [])
        for skill in skill_gaps[:2]:
            questions.append({
                "question": f"How would you approach learning {skill} for this role?",
                "type": "technical",
                "difficulty": "medium"
            })
        
        # Add role-specific questions
        if "engineer" in role.lower():
            questions.append({
                "question": "Walk me through your problem-solving process for a complex technical issue",
                "type": "technical",
                "difficulty": "hard"
            })
        
        return questions
    
    def _determine_next_action(self, session: InterviewSession, response: str) -> str:
        """Determine next action based on response quality"""
        response_length = len(response.split())
        
        # Simple heuristics for demo
        if response_length < 10:
            return "follow_up"  # Too short, need more detail
        elif response_length > 100:
            return "next_question"  # Good detailed answer
        elif session.current_question_index < 2:
            return "next_question"  # Early questions, keep moving
        else:
            return "next_question"
    
    def _generate_follow_up(self, session: InterviewSession, response: str) -> str:
        """Generate follow-up question"""
        follow_ups = [
            "Can you provide more specific details about that?",
            "What was the most challenging part of that experience?",
            "How did you measure the success of that approach?",
            "What would you do differently if you faced that situation again?"
        ]
        return follow_ups[len(session.responses) % len(follow_ups)]
    
    def _adjust_question_difficulty(self, session: InterviewSession) -> List[Dict[str, Any]]:
        """Add questions based on performance"""
        # Simple implementation - add one adaptive question
        avg_response_length = sum(len(r["response"].split()) for r in session.responses) / len(session.responses)
        
        if avg_response_length > 50:  # Good responses, add harder question
            return [{
                "question": "Describe a time when you had to make a difficult technical decision with limited information",
                "type": "behavioral",
                "difficulty": "hard"
            }]
        else:  # Shorter responses, add easier question
            return [{
                "question": "What interests you most about this role?",
                "type": "behavioral", 
                "difficulty": "easy"
            }]
