from bedrock_agentcore.runtime import BedrockAgentCoreApp
import boto3
import json
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handling import safe_aws_call, handle_agent_error
from utils.logging_config import cost_logger, log_with_context
from utils.memory_service import memory_service
from config.settings import settings
import logging
import uuid

os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

app = BedrockAgentCoreApp()

class MultiAccountCostIntelligenceAgent:
    def __init__(self):
        self.organizations = None
        self.is_org_account = False
        self.org_accounts = []
        self.current_account_id = None
        
        self._discover_environment()
    
    def _discover_environment(self):
        """Auto-discover AWS environment and capabilities"""
        try:
            # Get current account ID
            sts = boto3.client('sts', region_name=settings.aws_region)
            identity = sts.get_caller_identity()
            self.current_account_id = identity['Account']
            
            # Check if this is an organization management account
            try:
                self.organizations = boto3.client('organizations', region_name=settings.aws_region)
                org_info = self.organizations.describe_organization()
                self.is_org_account = True
                
                # Get all accounts in organization
                accounts = self.organizations.list_accounts()
                self.org_accounts = [
                    {'id': acc['Id'], 'name': acc['Name'], 'status': acc['Status']}
                    for acc in accounts['Accounts'] if acc['Status'] == 'ACTIVE'
                ]
                
            except Exception:
                # Not an org account or no permissions
                self.is_org_account = False
                self.org_accounts = [{'id': self.current_account_id, 'name': 'current', 'status': 'ACTIVE'}]
                
        except Exception as e:
            cost_logger.error(f"Environment discovery failed: {e}")
            self.current_account_id = 'unknown'

    def get_multi_account_costs(self):
        """Get complete cost picture across all organization accounts"""
        if self.is_org_account:
            return self._get_organization_wide_costs()
        else:
            return self._get_single_account_costs()
    
    def _get_organization_wide_costs(self):
        """Get costs across all organization accounts using cross-account access"""
        print("🏢 Collecting costs across all organization accounts...")
        
        total_usage = 0
        total_credits = 0
        account_results = []
        successful_accounts = 0
        
        for account in self.org_accounts:
            account_id = account['id']
            account_name = account['name']
            
            try:
                # Get costs for this specific account
                account_costs = self._get_account_costs(account_id, account_name)
                
                if account_costs['success']:
                    total_usage += account_costs['usage_cost']
                    total_credits += account_costs['credit_cost']
                    successful_accounts += 1
                    
                account_results.append(account_costs)
                
            except Exception as e:
                print(f"   ⚠️  Failed to get costs for {account_name}: {e}")
                account_results.append({
                    'account_id': account_id,
                    'account_name': account_name,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'total_usage_cost': total_usage,
            'total_credit_cost': total_credits,
            'total_net_cost': total_usage + total_credits,
            'accounts_checked': len(self.org_accounts),
            'successful_accounts': successful_accounts,
            'accounts': account_results,
            'cost_breakdown': {
                'usage_before_credits': total_usage,
                'credits_applied': abs(total_credits),
                'final_bill': total_usage + total_credits
            }
        }
    
    def _get_account_costs(self, account_id, account_name):
        """Get costs for a specific account using assume role or direct access"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            # If this is the current account, use direct access
            if account_id == self.current_account_id:
                ce = boto3.client('ce', region_name=settings.aws_region)
            else:
                # Use cross-account access
                sts = boto3.client('sts', region_name=settings.aws_region)
                role_arn = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
                
                assumed_role = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=f"cost-analysis-{account_id}",
                    ExternalId="aws-operations-command-center"
                )
                
                credentials = assumed_role['Credentials']
                ce = boto3.client(
                    'ce',
                    region_name=settings.aws_region,
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            
            # Get costs by record type
            result = safe_aws_call(
                ce.get_cost_and_usage,
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'RECORD_TYPE'}]
            )
            
            if result['success']:
                usage_cost = 0
                credit_cost = 0
                
                for time_period in result['data']['ResultsByTime']:
                    for group in time_period['Groups']:
                        record_type = group['Keys'][0]
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        
                        if record_type == 'Usage':
                            usage_cost += cost
                        elif record_type == 'Credit':
                            credit_cost += cost
                
                print(f"   ✅ {account_name}: Usage=${usage_cost:.2f}, Credits=${credit_cost:.2f}")
                
                return {
                    'account_id': account_id,
                    'account_name': account_name,
                    'usage_cost': usage_cost,
                    'credit_cost': credit_cost,
                    'net_cost': usage_cost + credit_cost,
                    'success': True
                }
            else:
                return {
                    'account_id': account_id,
                    'account_name': account_name,
                    'success': False,
                    'error': result['error']
                }
                
        except Exception as e:
            return {
                'account_id': account_id,
                'account_name': account_name,
                'success': False,
                'error': str(e)
            }
    
    def _get_single_account_costs(self):
        """Get costs for single account (fallback)"""
        ce = boto3.client('ce', region_name=settings.aws_region)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        result = safe_aws_call(
            ce.get_cost_and_usage,
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'RECORD_TYPE'}]
        )
        
        if result['success']:
            usage_cost = 0
            credit_cost = 0
            
            for time_period in result['data']['ResultsByTime']:
                for group in time_period['Groups']:
                    record_type = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if record_type == 'Usage':
                        usage_cost += cost
                    elif record_type == 'Credit':
                        credit_cost += cost
            
            return {
                'success': True,
                'total_usage_cost': usage_cost,
                'total_credit_cost': credit_cost,
                'total_net_cost': usage_cost + credit_cost,
                'accounts_checked': 1,
                'successful_accounts': 1,
                'account_id': self.current_account_id,
                'cost_breakdown': {
                    'usage_before_credits': usage_cost,
                    'credits_applied': abs(credit_cost),
                    'final_bill': usage_cost + credit_cost
                }
            }
        else:
            return {'success': False, 'error': result['error']}
        """Get costs for a specific account using its profile"""
        log_with_context(cost_logger, logging.INFO, "Starting cost collection", 
                        account=account_name, 
                        profile=profile_name,
                        date_range=f"{start_date} to {end_date}")
        
        try:
            # Create session with profile
            if profile_name == 'default':
                session = boto3.Session()
            else:
                session = boto3.Session(profile_name=profile_name)
            
            ce = session.client('ce', region_name=settings.aws_region)
            
            # Get costs by record type with error handling
            cost_result = safe_aws_call(
                ce.get_cost_and_usage,
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'RECORD_TYPE'}]
            )
            
            if not cost_result['success']:
                log_with_context(cost_logger, logging.ERROR, "Failed to get costs by record type", 
                                account=account_name,
                                error=cost_result['error'])
                return {
                    'account_name': account_name,
                    'profile': profile_name,
                    'success': False,
                    'error': cost_result['error']
                }
            
            # Process cost data
            usage_cost = 0
            credit_cost = 0
            
            for result in cost_result['data']['ResultsByTime']:
                for group in result['Groups']:
                    record_type = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if record_type == 'Usage':
                        usage_cost = cost
                    elif record_type == 'Credit':
                        credit_cost = cost
            
            # Get service breakdown if there are usage costs
            services = []
            if usage_cost > 0:
                service_result = safe_aws_call(
                    ce.get_cost_and_usage,
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
                    Filter={'Dimensions': {'Key': 'RECORD_TYPE', 'Values': ['Usage']}}
                )
                
                if service_result['success']:
                    for result in service_result['data']['ResultsByTime']:
                        for group in result['Groups']:
                            service = group['Keys'][0]
                            cost = float(group['Metrics']['UnblendedCost']['Amount'])
                            if cost > 0:
                                services.append({
                                    'service': service,
                                    'cost': round(cost, 2),
                                    'percentage': round((cost / usage_cost * 100), 1)
                                })
                    
                    services.sort(key=lambda x: x['cost'], reverse=True)
            
            log_with_context(cost_logger, logging.INFO, "Cost collection completed", 
                           account=account_name,
                           usage_cost=usage_cost,
                           credit_cost=credit_cost,
                           services_count=len(services))
            
            return {
                'account_name': account_name,
                'profile': profile_name,
                'usage_cost': round(usage_cost, 2),
                'credit_cost': round(credit_cost, 2),
                'net_cost': round(usage_cost + credit_cost, 2),
                'services': services[:10],
                'success': True
            }
            
        except Exception as e:
            return handle_agent_error('cost_intelligence', 'get_account_costs', e)

    def get_cost_forecast(self):
        """Get cost forecast from management account"""
        try:
            ce = boto3.client('ce', region_name='us-east-1')
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=90)
            
            forecast = ce.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Metric='BLENDED_COST',
                Granularity='MONTHLY'
            )
            
            total_forecast = float(forecast['Total']['Amount'])
            monthly_average = total_forecast / 3
            
            return {
                'total_forecast': round(total_forecast, 2),
                'monthly_average': round(monthly_average, 2)
            }
            
        except Exception as e:
            print(f"❌ Cost forecast failed: {e}")
            return None

    def get_optimization_opportunities(self):
        """Get optimization opportunities from management account"""
        opportunities = []
        total_savings = 0
        
        try:
            ec2 = boto3.client('ec2', region_name='us-east-1')
            
            # Check for unused EBS volumes
            volumes = ec2.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )
            
            for volume in volumes['Volumes']:
                size = volume['Size']
                volume_type = volume.get('VolumeType', 'gp2')
                pricing = {'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'io2': 0.125}
                monthly_cost = size * pricing.get(volume_type, 0.10)
                
                opportunities.append({
                    'type': 'unused_ebs_volume',
                    'resource_id': volume['VolumeId'],
                    'monthly_savings': round(monthly_cost, 2),
                    'recommendation': f'Delete unused {size}GB {volume_type} volume',
                    'risk': 'low'
                })
                total_savings += monthly_cost
                
        except Exception as e:
            print(f"Optimization analysis failed: {e}")
        
        return {
            'opportunities': opportunities,
            'total_potential_monthly_savings': round(total_savings, 2),
            'data_source': 'multi_account_optimization_analysis'
        }

agent = MultiAccountCostIntelligenceAgent()

@app.entrypoint
def invoke(payload):
    """Multi-Account Cost Intelligence Agent - True organization-wide costs"""
    session_id = payload.get('session_id', str(uuid.uuid4()))
    
    try:
        # Store session context
        memory_service.store_context(session_id, {
            'agent': 'cost_intelligence',
            'timestamp': datetime.now().isoformat(),
            'payload': payload
        })
        
        action = payload.get("action", "analyze")
        
        if action == "full_analysis":
            print("🏢 Starting multi-account cost analysis...")
            
            # Get costs across all configured accounts
            multi_account_costs = agent.get_multi_account_costs()
            
            # Get forecast and optimizations
            forecast = agent.get_cost_forecast()
            optimizations = agent.get_optimization_opportunities()
            
            result = {
                'cost_analysis': {
                    'current_monthly_cost': multi_account_costs['total_usage_cost'],
                    'cost_type': 'multi_account_usage',
                    'total_usage_cost': multi_account_costs['total_usage_cost'],
                    'total_credit_cost': multi_account_costs['total_credit_cost'],
                    'total_net_cost': multi_account_costs['total_net_cost'],
                    'forecasted_monthly_cost': forecast['monthly_average'] if forecast else 0,
                    'forecasted_90_day_cost': forecast['total_forecast'] if forecast else 0,
                    'trend': 'stable',
                    'top_services': multi_account_costs['aggregated_services'],
                    'account_breakdown': multi_account_costs['account_results'],
                    'data_source': multi_account_costs['data_source'],
                    'is_organization': agent.is_org_account,
                    'organization_accounts': len(agent.org_accounts) if agent.is_org_account else 1,
                    'accounts_checked': multi_account_costs['accounts_checked'],
                    'successful_accounts': multi_account_costs['successful_accounts']
                },
                'optimizations': optimizations,
                'summary': {
                    'potential_monthly_savings': optimizations['total_potential_monthly_savings'],
                    'cost_trend': 'stable',
                    'data_source': 'multi_account_comprehensive_analysis',
                    'shows_true_org_costs': True,
                    'accounts_analyzed': multi_account_costs['successful_accounts']
                }
            }
                
        else:
            result = {
                'message': f'Multi-Account Cost Intelligence Agent ready! Checks costs across {len(agent.account_profiles)} configured accounts.',
                'available_actions': ['full_analysis'],
                'configured_accounts': list(agent.account_profiles.keys()),
                'capabilities': ['multi_account_costs', 'true_organization_analysis', 'cross_account_aggregation']
            }
        
        result['agent'] = 'cost_intelligence_multi_account'
        result['timestamp'] = datetime.now().isoformat()
        result['success'] = True
        result['services_used'] = ['runtime', 'memory', 'gateway']
        
        return result
        
    except Exception as e:
        return {
            'agent': 'cost_intelligence_multi_account',
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    app.run()
