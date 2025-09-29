"""
AWS Operations Command Center - Agent Input/Output Schemas
Pydantic schemas for validating agent requests and responses.
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class ActionType(str, Enum):
    """Valid action types for agents"""
    FULL_ANALYSIS = "full_analysis"
    FORECAST = "forecast"
    OPTIMIZATION = "optimization"
    ASSESS_EXISTING = "assess_existing"
    GENERATE_ARCHITECTURE = "generate_architecture"
    FULL_OPERATIONS_ANALYSIS = "full_operations_analysis"

class ScaleType(str, Enum):
    """Valid scale types for infrastructure"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class CostAnalysisRequest(BaseModel):
    """Schema for cost intelligence agent requests"""
    action: ActionType = ActionType.FULL_ANALYSIS
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    accounts: Optional[List[str]] = None
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v

class InfrastructureRequest(BaseModel):
    """Schema for infrastructure intelligence agent requests"""
    action: ActionType = ActionType.ASSESS_EXISTING
    requirements: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "action": "generate_architecture",
                "requirements": {
                    "type": "web_app_3tier",
                    "scale": "medium",
                    "budget_limit": 1000
                }
            }
        }

class OperationsRequest(BaseModel):
    """Schema for operations intelligence agent requests"""
    action: ActionType = ActionType.FULL_OPERATIONS_ANALYSIS
    services: Optional[List[str]] = None
    timeout: Optional[int] = Field(default=60, ge=10, le=300)
    
    @validator('services')
    def validate_services(cls, v):
        if v is not None:
            valid_services = ['ec2', 'rds', 's3', 'elbv2', 'cloudwatch']
            invalid = [s for s in v if s not in valid_services]
            if invalid:
                raise ValueError(f'Invalid services: {invalid}. Valid: {valid_services}')
        return v

class AgentResponse(BaseModel):
    """Base schema for agent responses"""
    success: bool
    agent: str
    operation: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
class CostAnalysisResponse(AgentResponse):
    """Schema for cost intelligence agent responses"""
    total_usage_cost: Optional[float] = None
    total_credit_cost: Optional[float] = None
    account_results: Optional[List[Dict[str, Any]]] = None
    
class InfrastructureResponse(AgentResponse):
    """Schema for infrastructure intelligence agent responses"""
    architecture_type: Optional[str] = None
    estimated_monthly_cost: Optional[float] = None
    security_score: Optional[int] = Field(None, ge=0, le=100)
    reliability_score: Optional[int] = Field(None, ge=0, le=100)

class OperationsResponse(AgentResponse):
    """Schema for operations intelligence agent responses"""
    total_resources: Optional[int] = None
    security_issues: Optional[List[Dict[str, Any]]] = None
    organization_context: Optional[Dict[str, Any]] = None

def validate_request(request_data: Dict[str, Any], schema_class: BaseModel) -> Dict[str, Any]:
    """
    Validate request data against schema
    
    Args:
        request_data: Raw request data
        schema_class: Pydantic schema class
    
    Returns:
        Validated data or error response
    """
    try:
        validated = schema_class(**request_data)
        return {'valid': True, 'data': validated.dict()}
    except Exception as e:
        return {'valid': False, 'errors': str(e)}
