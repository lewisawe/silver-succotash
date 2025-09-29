"""
Tests for cost intelligence agent
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent

class TestCostIntelligenceAgent:
    
    @patch('agent.cost_intelligence_agent.safe_aws_call')
    def test_init_with_organizations(self, mock_safe_call):
        """Test agent initialization with Organizations"""
        # Mock successful Organizations call
        mock_safe_call.side_effect = [
            {
                'success': True,
                'data': {'Organization': {'Id': 'o-test123'}}
            },
            {
                'success': True,
                'data': {
                    'Accounts': [
                        {'Id': '123456789012', 'Name': 'Account1', 'Status': 'ACTIVE'},
                        {'Id': '123456789013', 'Name': 'Account2', 'Status': 'ACTIVE'}
                    ]
                }
            }
        ]
        
        agent = MultiAccountCostIntelligenceAgent()
        
        assert agent.is_org_account is True
        assert len(agent.org_accounts) == 2
        assert agent.org_accounts[0]['name'] == 'Account1'
    
    @patch('agent.cost_intelligence_agent.safe_aws_call')
    def test_init_without_organizations(self, mock_safe_call):
        """Test agent initialization without Organizations"""
        # Mock failed Organizations call
        mock_safe_call.return_value = {
            'success': False,
            'error': 'access_denied'
        }
        
        agent = MultiAccountCostIntelligenceAgent()
        
        assert agent.is_org_account is False
        assert len(agent.org_accounts) == 0
    
    @patch('boto3.Session')
    @patch('agent.cost_intelligence_agent.safe_aws_call')
    def test_get_account_costs_success(self, mock_safe_call, mock_session):
        """Test successful cost collection"""
        # Mock AWS session and client
        mock_ce = Mock()
        mock_session.return_value.client.return_value = mock_ce
        
        # Mock Organizations call to fail (so agent doesn't try to initialize orgs)
        # Then mock successful cost API calls
        mock_safe_call.side_effect = [
            {'success': False, 'error': 'access_denied'},  # Organizations call
            {
                'success': True,
                'data': {
                    'ResultsByTime': [{
                        'Groups': [
                            {'Keys': ['Usage'], 'Metrics': {'UnblendedCost': {'Amount': '100.50'}}},
                            {'Keys': ['Credit'], 'Metrics': {'UnblendedCost': {'Amount': '-50.25'}}}
                        ]
                    }]
                }
            },
            {
                'success': True,
                'data': {
                    'ResultsByTime': [{
                        'Groups': [
                            {'Keys': ['Amazon EC2'], 'Metrics': {'UnblendedCost': {'Amount': '60.30'}}},
                            {'Keys': ['Amazon RDS'], 'Metrics': {'UnblendedCost': {'Amount': '40.20'}}}
                        ]
                    }]
                }
            }
        ]
        
        agent = MultiAccountCostIntelligenceAgent()
        result = agent.get_account_costs('default', 'test-account', '2024-01-01', '2024-01-31')
        
        assert result['success'] is True
        assert result['account_name'] == 'test-account'
        assert result['usage_cost'] == 100.50
        assert result['credit_cost'] == -50.25
        assert result['net_cost'] == 50.25
        assert len(result['services']) == 2
        assert result['services'][0]['service'] == 'Amazon EC2'
    
    @patch('boto3.Session')
    @patch('agent.cost_intelligence_agent.safe_aws_call')
    def test_get_account_costs_api_failure(self, mock_safe_call, mock_session):
        """Test cost collection with API failure"""
        # Mock AWS session
        mock_ce = Mock()
        mock_session.return_value.client.return_value = mock_ce
        
        # Mock failed API call
        mock_safe_call.return_value = {
            'success': False,
            'error': 'access_denied',
            'error_code': 'AccessDenied'
        }
        
        agent = MultiAccountCostIntelligenceAgent()
        result = agent.get_account_costs('default', 'test-account', '2024-01-01', '2024-01-31')
        
        assert result['success'] is False
        assert result['error'] == 'access_denied'
        assert result['account_name'] == 'test-account'
    
    @patch('agent.cost_intelligence_agent.safe_aws_call')
    def test_get_multi_account_costs(self, mock_safe_call):
        """Test multi-account cost collection"""
        # Mock Organizations calls
        mock_safe_call.side_effect = [
            {'success': False, 'error': 'access_denied'},  # Organizations call fails
        ]
        
        agent = MultiAccountCostIntelligenceAgent()
        
        # Mock the get_account_costs method
        with patch.object(agent, 'get_account_costs') as mock_get_costs:
            # Need to provide enough mock responses for all 3 profiles
            mock_get_costs.side_effect = [
                {
                    'success': True,
                    'account_name': 'management',
                    'usage_cost': 75.00,
                    'credit_cost': -25.00,
                    'services': [{'service': 'EC2', 'cost': 50.00, 'percentage': 66.7}]
                },
                {
                    'success': True,
                    'account_name': 'crummyfun',
                    'usage_cost': 50.00,
                    'credit_cost': -10.00,
                    'services': [{'service': 'RDS', 'cost': 30.00, 'percentage': 60.0}]
                },
                {
                    'success': True,
                    'account_name': 'achamin',
                    'usage_cost': 25.00,
                    'credit_cost': -5.00,
                    'services': [{'service': 'S3', 'cost': 15.00, 'percentage': 60.0}]
                }
            ]
            
            result = agent.get_multi_account_costs()
            
            assert result['total_usage_cost'] == 150.00
            assert result['total_credit_cost'] == -40.00
            assert result['total_net_cost'] == 110.00
            assert result['successful_accounts'] == 3
            assert len(result['aggregated_services']) == 3
    
    def test_account_profiles_configuration(self):
        """Test that account profiles are properly configured"""
        with patch('agent.cost_intelligence_agent.safe_aws_call') as mock_safe_call:
            mock_safe_call.return_value = {'success': False, 'error': 'access_denied'}
            
            agent = MultiAccountCostIntelligenceAgent()
            
            # Should have profiles from settings
            assert 'management' in agent.account_profiles
            assert 'crummyfun' in agent.account_profiles
            assert len(agent.account_profiles) >= 2
