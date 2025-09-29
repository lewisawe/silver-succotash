"""
AWS Operations Command Center - Health Check Endpoints
Provides health monitoring for the application and AWS connectivity.
"""

from flask import Blueprint, jsonify
import boto3
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handling import safe_aws_call
from utils.logging_config import api_logger, log_with_context
from config.settings import settings
import logging

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'environment': os.getenv('ENVIRONMENT', 'development')
    })

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check including AWS connectivity"""
    log_with_context(api_logger, logging.INFO, "Detailed health check requested")
    
    checks = {
        'aws_credentials': check_aws_credentials(),
        'cost_explorer': check_cost_explorer(),
        'organizations': check_organizations(),
        'configuration': check_configuration()
    }
    
    overall_status = 'healthy' if all(check['status'] for check in checks.values()) else 'unhealthy'
    
    response = {
        'status': overall_status,
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat(),
        'region': settings.aws_region
    }
    
    log_with_context(api_logger, logging.INFO, "Health check completed", 
                    overall_status=overall_status,
                    failed_checks=[name for name, check in checks.items() if not check['status']])
    
    return jsonify(response)

def check_aws_credentials():
    """Check AWS credentials validity"""
    try:
        result = safe_aws_call(lambda: boto3.client('sts').get_caller_identity())
        if result['success']:
            return {
                'status': True,
                'message': 'AWS credentials valid',
                'account_id': result['data'].get('Account', 'unknown')
            }
        else:
            return {
                'status': False,
                'message': f"AWS credentials invalid: {result['error']}"
            }
    except Exception as e:
        return {
            'status': False,
            'message': f"Error checking credentials: {str(e)}"
        }

def check_cost_explorer():
    """Check Cost Explorer API connectivity"""
    try:
        ce = boto3.client('ce', region_name=settings.aws_region)
        
        # Simple API call to test connectivity
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = safe_aws_call(
            ce.get_cost_and_usage,
            TimePeriod={'Start': yesterday, 'End': today},
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        if result['success']:
            return {
                'status': True,
                'message': 'Cost Explorer accessible'
            }
        else:
            return {
                'status': False,
                'message': f"Cost Explorer error: {result['error']}"
            }
    except Exception as e:
        return {
            'status': False,
            'message': f"Cost Explorer check failed: {str(e)}"
        }

def check_organizations():
    """Check Organizations API connectivity"""
    try:
        result = safe_aws_call(
            lambda: boto3.client('organizations', region_name=settings.aws_region).describe_organization()
        )
        
        if result['success']:
            return {
                'status': True,
                'message': 'Organizations accessible',
                'organization_id': result['data']['Organization']['Id']
            }
        else:
            return {
                'status': False,
                'message': f"Organizations error: {result['error']}"
            }
    except Exception as e:
        return {
            'status': False,
            'message': f"Organizations check failed: {str(e)}"
        }

def check_configuration():
    """Check configuration validity"""
    try:
        settings.validate()
        return {
            'status': True,
            'message': 'Configuration valid',
            'profiles': list(settings.aws_profiles.keys())
        }
    except Exception as e:
        return {
            'status': False,
            'message': f"Configuration invalid: {str(e)}"
        }

@health_bp.route('/health/agents')
def agents_health_check():
    """Check agent availability"""
    agents_status = {}
    
    # Test each agent
    try:
        from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
        agent = MultiAccountCostIntelligenceAgent()
        agents_status['cost_intelligence'] = {
            'status': True,
            'message': 'Agent initialized successfully',
            'profiles': len(agent.account_profiles),
            'organization': agent.is_org_account
        }
    except Exception as e:
        agents_status['cost_intelligence'] = {
            'status': False,
            'message': f"Agent initialization failed: {str(e)}"
        }
    
    try:
        from agent.operations_intelligence_agent import OrganizationsOperationsIntelligenceAgent
        agent = OrganizationsOperationsIntelligenceAgent()
        agents_status['operations_intelligence'] = {
            'status': True,
            'message': 'Agent initialized successfully',
            'organization': agent.is_org_account
        }
    except Exception as e:
        agents_status['operations_intelligence'] = {
            'status': False,
            'message': f"Agent initialization failed: {str(e)}"
        }
    
    # Infrastructure agent is function-based, just check import
    try:
        from agent.infrastructure_intelligence_agent import invoke
        agents_status['infrastructure_intelligence'] = {
            'status': True,
            'message': 'Agent available'
        }
    except Exception as e:
        agents_status['infrastructure_intelligence'] = {
            'status': False,
            'message': f"Agent import failed: {str(e)}"
        }
    
    overall_status = 'healthy' if all(agent['status'] for agent in agents_status.values()) else 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'agents': agents_status,
        'timestamp': datetime.utcnow().isoformat()
    })
