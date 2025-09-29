import boto3
import json
import base64
import os
from typing import Dict, Any, Optional

# Ensure us-east-1 region
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

class NovaVoiceProcessor:
    """Nova Sonic voice processing for interview agent - us-east-1"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=region_name,
            config=boto3.session.Config(
                retries={'max_attempts': 3},
                read_timeout=30,
                connect_timeout=10
            )
        )
        self.model_id = "amazon.nova-sonic-v1:0"
    
    def speech_to_text(self, audio_data: str, audio_format: str = "wav") -> Dict[str, Any]:
        """Convert speech to text using Nova Sonic"""
        try:
            request_body = {
                "inputAudio": {
                    "format": audio_format,
                    "source": {
                        "bytes": audio_data
                    }
                },
                "task": "transcription",
                "inferenceConfig": {
                    "temperature": 0.1,
                    "maxTokens": 1000
                }
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            result = json.loads(response['body'].read())
            
            transcript = result.get('transcript', {})
            text = transcript.get('text', '')
            confidence = transcript.get('confidence', 0.0)
            
            return {
                "success": True,
                "text": text,
                "confidence": confidence,
                "audio_duration": transcript.get('duration', 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def text_to_speech(self, text: str, voice: str = "neutral") -> Dict[str, Any]:
        """Convert text to speech using Nova Sonic"""
        try:
            if len(text) > 1000:
                text = text[:1000] + "..."
            
            request_body = {
                "inputText": text,
                "task": "synthesis",
                "inferenceConfig": {
                    "voice": voice,
                    "speed": 1.0,
                    "pitch": 1.0
                }
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            result = json.loads(response['body'].read())
            
            audio_data = result.get('audioData', '')
            audio_format = result.get('audioFormat', 'wav')
            
            return {
                "success": True,
                "audio_data": audio_data,
                "audio_format": audio_format,
                "text_length": len(text)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "audio_data": ""
            }
    
    def process_interview_audio(self, audio_data: str, question: str = "") -> Dict[str, Any]:
        """Process interview audio with context"""
        stt_result = self.speech_to_text(audio_data)
        
        if not stt_result["success"]:
            return {
                "success": False,
                "error": f"Speech recognition failed: {stt_result['error']}"
            }
        
        transcript = stt_result["text"]
        confidence = stt_result["confidence"]
        
        if len(transcript.strip()) < 5:
            return {
                "success": False,
                "error": "Audio too short or unclear"
            }
        
        if confidence < 0.5:
            return {
                "success": False,
                "error": "Low audio quality, please try again"
            }
        
        return {
            "success": True,
            "transcript": transcript,
            "confidence": confidence,
            "word_count": len(transcript.split()),
            "question_context": question
        }
    
    def generate_interview_audio(self, text: str, voice_style: str = "professional") -> Dict[str, Any]:
        """Generate interview audio with appropriate voice"""
        voice_mapping = {
            "professional": "neutral",
            "friendly": "friendly", 
            "formal": "neutral"
        }
        
        voice = voice_mapping.get(voice_style, "neutral")
        formatted_text = self._format_for_speech(text)
        
        return self.text_to_speech(formatted_text, voice)
    
    def _format_for_speech(self, text: str) -> str:
        """Format text for better speech synthesis"""
        text = text.replace(". ", ". ... ")
        text = text.replace("? ", "? ... ")
        text = text.replace(": ", ": ... ")
        
        replacements = {
            "API": "A P I",
            "REST": "R E S T",
            "JSON": "J S O N",
            "SQL": "S Q L",
            "AWS": "A W S"
        }
        
        for term, pronunciation in replacements.items():
            text = text.replace(term, pronunciation)
        
        return text
