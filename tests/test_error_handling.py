"""
Tests for error handling utilities
"""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError, NoCredentialsError

from utils.error_handling import safe_aws_call, handle_agent_error, AWSOperationsError

class TestSafeAWSCall:
    
    def test_successful_call(self):
        """Test successful AWS API call"""
        mock_func = Mock(return_value={'data': 'success'})
        mock_func.__self__ = Mock()
        mock_func.__self__._service_model = Mock()
        mock_func.__self__._service_model.service_name = 'test-service'
        mock_func.__name__ = 'test_operation'
        
        result = safe_aws_call(mock_func)
        
        assert result['success'] is True
        assert result['data'] == {'data': 'success'}
        mock_func.assert_called_once()
    
    def test_access_denied_error(self):
        """Test AccessDenied error handling"""
        mock_func = Mock()
        mock_func.__self__ = Mock()
        mock_func.__self__._service_model = Mock()
        mock_func.__self__._service_model.service_name = 'test-service'
        mock_func.__name__ = 'test_operation'
        
        error = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'TestOperation'
        )
        mock_func.side_effect = error
        
        result = safe_aws_call(mock_func)
        
        assert result['success'] is False
        assert result['error'] == 'access_denied'
        assert result['error_code'] == 'AccessDenied'
        assert result['service'] == 'test-service'
    
    def test_throttling_with_retry(self):
        """Test throttling error with successful retry"""
        mock_func = Mock()
        mock_func.__self__ = Mock()
        mock_func.__self__._service_model = Mock()
        mock_func.__self__._service_model.service_name = 'test-service'
        mock_func.__name__ = 'test_operation'
        
        # First call fails with throttling, second succeeds
        throttling_error = ClientError(
            {'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
            'TestOperation'
        )
        mock_func.side_effect = [throttling_error, {'data': 'success'}]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = safe_aws_call(mock_func, max_retries=2)
        
        assert result['success'] is True
        assert result['data'] == {'data': 'success'}
        assert mock_func.call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test max retries exceeded for throttling"""
        mock_func = Mock()
        mock_func.__self__ = Mock()
        mock_func.__self__._service_model = Mock()
        mock_func.__self__._service_model.service_name = 'test-service'
        mock_func.__name__ = 'test_operation'
        
        throttling_error = ClientError(
            {'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
            'TestOperation'
        )
        mock_func.side_effect = throttling_error
        
        with patch('time.sleep'):
            result = safe_aws_call(mock_func, max_retries=2)
        
        assert result['success'] is False
        assert result['error'] == 'max_retries_exceeded'
        assert mock_func.call_count == 2
    
    def test_no_credentials_error(self):
        """Test NoCredentialsError handling"""
        mock_func = Mock()
        mock_func.__self__ = Mock()
        mock_func.__self__._service_model = Mock()
        mock_func.__self__._service_model.service_name = 'test-service'
        mock_func.__name__ = 'test_operation'
        
        mock_func.side_effect = NoCredentialsError()
        
        result = safe_aws_call(mock_func)
        
        assert result['success'] is False
        assert result['error'] == 'no_credentials'
        assert 'credentials' in result['message'].lower()

class TestHandleAgentError:
    
    def test_handle_agent_error(self):
        """Test agent error handling"""
        error = ValueError("Test error message")
        
        result = handle_agent_error('test_agent', 'test_operation', error)
        
        assert result['success'] is False
        assert result['agent'] == 'test_agent'
        assert result['operation'] == 'test_operation'
        assert result['error'] == 'ValueError'
        assert result['message'] == 'Test error message'
        assert 'timestamp' in result
