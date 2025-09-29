"""
AWS Operations Command Center - Error Handling Utilities
Provides robust error handling for AWS API calls and agent operations.
"""

from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
import time
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

class AWSOperationsError(Exception):
    """Custom exception for AWS Operations Command Center"""
    def __init__(self, service: str, operation: str, original_error: Exception):
        self.service = service
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"{service}.{operation}: {original_error}")

def safe_aws_call(func: Callable, *args, max_retries: int = 3, **kwargs) -> Dict[str, Any]:
    """
    Wrapper for AWS API calls with retry logic and proper error handling
    
    Args:
        func: AWS API function to call
        max_retries: Maximum number of retry attempts
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Dict containing either the result or error information
    """
    # Extract service name more safely
    service_name = 'unknown'
    try:
        if hasattr(func, '__self__') and hasattr(func.__self__, '_service_model'):
            service_name = func.__self__._service_model.service_name
    except:
        pass
    
    operation_name = getattr(func, '__name__', 'unknown_operation')
    
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            logger.info(f"AWS API call successful", extra={
                'service': service_name,
                'operation': operation_name,
                'attempt': attempt + 1
            })
            return {'success': True, 'data': result}
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.warning(f"AWS API error", extra={
                'service': service_name,
                'operation': operation_name,
                'error_code': error_code,
                'attempt': attempt + 1,
                'max_retries': max_retries
            })
            
            # Handle retryable errors
            if error_code in ['Throttling', 'RequestLimitExceeded', 'ServiceUnavailable']:
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt
                    logger.info(f"Retrying after {sleep_time} seconds")
                    time.sleep(sleep_time)
                    continue
                else:
                    return {
                        'success': False,
                        'error': 'max_retries_exceeded',
                        'error_code': error_code,
                        'message': f"Max retries exceeded for {error_code}",
                        'service': service_name
                    }
            
            # Handle non-retryable errors
            elif error_code == 'AccessDenied':
                return {
                    'success': False,
                    'error': 'access_denied',
                    'error_code': error_code,
                    'message': f"Access denied for {service_name}.{operation_name}",
                    'service': service_name
                }
            
            elif error_code in ['InvalidParameterValue', 'ValidationException']:
                return {
                    'success': False,
                    'error': 'invalid_parameters',
                    'error_code': error_code,
                    'message': error_message,
                    'service': service_name
                }
            
            else:
                # Unknown error, don't retry
                return {
                    'success': False,
                    'error': 'aws_client_error',
                    'error_code': error_code,
                    'message': error_message,
                    'service': service_name
                }
                
        except NoCredentialsError:
            logger.error(f"No AWS credentials found", extra={
                'service': service_name,
                'operation': operation_name
            })
            return {
                'success': False,
                'error': 'no_credentials',
                'message': 'AWS credentials not found or invalid',
                'service': service_name
            }
            
        except BotoCoreError as e:
            logger.error(f"BotoCore error", extra={
                'service': service_name,
                'operation': operation_name,
                'error': str(e)
            })
            return {
                'success': False,
                'error': 'botocore_error',
                'message': str(e),
                'service': service_name
            }
            
        except Exception as e:
            logger.error(f"Unexpected error", extra={
                'service': service_name,
                'operation': operation_name,
                'error': str(e),
                'error_type': type(e).__name__
            })
            return {
                'success': False,
                'error': 'unexpected_error',
                'message': str(e),
                'service': service_name
            }
    
    # Should never reach here, but just in case
    return {
        'success': False,
        'error': 'unknown_error',
        'message': 'Unknown error occurred',
        'service': service_name
    }

def handle_agent_error(agent_name: str, operation: str, error: Exception) -> Dict[str, Any]:
    """
    Standardized error handling for agent operations
    
    Args:
        agent_name: Name of the agent (e.g., 'cost_intelligence')
        operation: Operation being performed
        error: The exception that occurred
    
    Returns:
        Standardized error response
    """
    logger.error(f"Agent error", extra={
        'agent': agent_name,
        'operation': operation,
        'error': str(error),
        'error_type': type(error).__name__
    })
    
    return {
        'success': False,
        'agent': agent_name,
        'operation': operation,
        'error': type(error).__name__,
        'message': str(error),
        'timestamp': time.time()
    }

def validate_aws_response(response: Dict[str, Any], required_fields: list) -> bool:
    """
    Validate AWS API response has required fields
    
    Args:
        response: AWS API response
        required_fields: List of required field names
    
    Returns:
        True if valid, False otherwise
    """
    for field in required_fields:
        if field not in response:
            logger.warning(f"Missing required field in AWS response: {field}")
            return False
    return True
