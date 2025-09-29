"""
AgentCore Gateway Client for true agent-to-agent communication
"""
import boto3
import json
from typing import Dict, Any
from utils.logging_config import api_logger

class AgentCoreGateway:
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
    
    def invoke_agent(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke agent through AgentCore gateway"""
        try:
            # Map agent names to actual AgentCore agent IDs (must be <=10 chars, alphanumeric)
            agent_mapping = {
                'cost_intelligence': 'COSTAGT001',
                'operations_intelligence': 'OPSAGT001', 
                'infrastructure_intelligence': 'INFRAAGT01'
            }
            
            agent_id = agent_mapping.get(agent_name)
            if not agent_id:
                return {'success': False, 'error': f'Unknown agent: {agent_name}'}
            
            response = self.bedrock_agent.invoke_agent(
                agentId=agent_id,
                agentAliasId='TSTALIASID',
                sessionId=payload.get('session_id', 'default'),
                inputText=json.dumps(payload)
            )
            
            # Parse response
            result = {}
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result = json.loads(chunk['bytes'].decode())
            
            return result
            
        except Exception as e:
            api_logger.error(f"Gateway invocation failed: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
gateway = AgentCoreGateway()
