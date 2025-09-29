"""
Memory service for cross-agent context sharing
"""
import json
import time
from typing import Any, Dict, Optional
from utils.logging_config import api_logger

class MemoryService:
    def __init__(self):
        self._memory = {}  # In-memory store for now
        self._ttl = {}     # TTL tracking
    
    def store_context(self, session_id: str, context: Dict[str, Any], ttl: int = 300) -> bool:
        """Store context with TTL"""
        try:
            # Serialize to check size
            serialized = json.dumps(context)
            if len(serialized) > 1024 * 1024:  # 1MB limit
                api_logger.warning(f"Context too large for session {session_id}")
                return False
            
            self._memory[session_id] = context
            self._ttl[session_id] = time.time() + ttl
            return True
        except Exception as e:
            api_logger.error(f"Failed to store context: {e}")
            return False
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve context if not expired"""
        try:
            if session_id not in self._memory:
                return None
            
            if time.time() > self._ttl.get(session_id, 0):
                # Expired
                self._memory.pop(session_id, None)
                self._ttl.pop(session_id, None)
                return None
            
            return self._memory[session_id]
        except Exception as e:
            api_logger.error(f"Failed to get context: {e}")
            return None

# Global instance
memory_service = MemoryService()
