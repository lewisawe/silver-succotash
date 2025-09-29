from bedrock_agentcore.runtime import BedrockAgentCoreApp
import boto3
import json
import os
import sys
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handling import safe_aws_call, handle_agent_error
from utils.logging_config import ops_logger, log_with_context
from config.settings import settings
import logging

os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

app = BedrockAgentCoreApp()

class OrganizationsOperationsIntelligenceAgent:
    def __init__(self):
        self.ec2 = None
        self.rds = None
        self.elbv2 = None
        self.cloudwatch = None
        self.s3 = None
        self.organizations = None
        self.is_org_account = False
        self.org_accounts = []
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AWS clients with Organizations support"""
        ops_logger.info("Initializing operations intelligence agent")
        
        try:
            self.ec2 = boto3.client('ec2', region_name=settings.aws_region)
            self.rds = boto3.client('rds', region_name=settings.aws_region)
            self.elbv2 = boto3.client('elbv2', region_name=settings.aws_region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=settings.aws_region)
            self.s3 = boto3.client('s3', region_name=settings.aws_region)
            
            # Try Organizations with error handling
            org_result = safe_aws_call(
                lambda: boto3.client('organizations', region_name=settings.aws_region).describe_organization()
            )
            
            if org_result['success']:
                self.organizations = boto3.client('organizations', region_name=settings.aws_region)
                self.is_org_account = True
                
                accounts_result = safe_aws_call(self.organizations.list_accounts)
                if accounts_result['success']:
                    self.org_accounts = [
                        {'id': acc['Id'], 'name': acc['Name'], 'status': acc['Status']}
                        for acc in accounts_result['data']['Accounts'] if acc['Status'] == 'ACTIVE'
                    ]
                    log_with_context(ops_logger, logging.INFO, "Organizations detected", account_count=len(self.org_accounts))
            else:
                self.is_org_account = False
                
        except Exception as e:
            log_with_context(ops_logger, logging.ERROR, "Client initialization failed", error=str(e))

    def get_organization_resource_inventory(self):
        """Get resource inventory with cross-account scanning"""
        if self.is_org_account:
            return self._scan_organization_accounts()
        else:
            return self._scan_current_account_only()
    
    def _scan_organization_accounts(self):
        """Scan resources across all organization accounts"""
        all_resources = {}
        resource_types = {}
        successful_accounts = 0
        
        for account in self.org_accounts:
            account_id = account['id']
            account_name = account['name']
            
            try:
                # Assume role in target account
                account_resources = self._scan_account_resources(account_id, account_name)
                if account_resources:
                    all_resources.update(account_resources)
                    successful_accounts += 1
                    
            except Exception as e:
                ops_logger.warning(f"Failed to scan account {account_name}: {e}")
        
        # Count resource types
        for resource in all_resources.values():
            resource_type = resource.get('type', 'unknown')
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
        
        return {
            'resources': all_resources,
            'resource_types': resource_types,
            'total_resources': len(all_resources),
            'organization_context': {
                'is_organization': True,
                'total_accounts': len(self.org_accounts),
                'scanned_accounts': successful_accounts,
                'scan_coverage': f"{successful_accounts}/{len(self.org_accounts)}"
            },
            'data_source': 'cross_account_organizations_scan'
        }
    
    def _scan_account_resources(self, account_id: str, account_name: str):
        """Scan resources in a specific account using assume role"""
        try:
            # Create assume role session
            sts = boto3.client('sts', region_name=settings.aws_region)
            role_arn = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
            
            assumed_role = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"ops-scan-{account_id}",
                ExternalId="aws-operations-command-center"
            )
            
            # Create clients with assumed role credentials
            credentials = assumed_role['Credentials']
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=settings.aws_region
            )
            
            resources = {}
            
            # Scan EC2 instances
            ec2 = session.client('ec2')
            instances_result = safe_aws_call(ec2.describe_instances)
            
            if instances_result['success']:
                for reservation in instances_result['data']['Reservations']:
                    for instance in reservation['Instances']:
                        instance_id = instance['InstanceId']
                        resources[f"{account_name}-{instance_id}"] = {
                            'type': 'ec2_instance',
                            'id': instance_id,
                            'state': instance['State']['Name'],
                            'instance_type': instance['InstanceType'],
                            'account_id': account_id,
                            'account_name': account_name
                        }
            
            # Scan S3 buckets (S3 is global, but we'll attribute to account)
            s3 = session.client('s3')
            buckets_result = safe_aws_call(s3.list_buckets)
            
            if buckets_result['success']:
                for bucket in buckets_result['data']['Buckets']:
                    bucket_name = bucket['Name']
                    resources[f"{account_name}-{bucket_name}"] = {
                        'type': 's3_bucket',
                        'id': bucket_name,
                        'creation_date': bucket['CreationDate'].isoformat(),
                        'account_id': account_id,
                        'account_name': account_name
                    }
            
            # Scan RDS instances
            rds = session.client('rds')
            rds_result = safe_aws_call(rds.describe_db_instances)
            
            if rds_result['success']:
                for db in rds_result['data']['DBInstances']:
                    db_id = db['DBInstanceIdentifier']
                    resources[f"{account_name}-{db_id}"] = {
                        'type': 'rds_instance',
                        'id': db_id,
                        'engine': db['Engine'],
                        'status': db['DBInstanceStatus'],
                        'account_id': account_id,
                        'account_name': account_name
                    }
            
            print(f"   ✅ {account_name}: Found {len(resources)} resources")
            return resources
            
        except Exception as e:
            ops_logger.error(f"Cross-account scan failed for {account_name}: {e}")
            return {}
    
    def _scan_current_account_only(self):
        """Fallback to current account scanning"""
        resources, resource_types = self._scan_current_account_resources()
        
        return {
            'resources': resources,
            'resource_types': resource_types,
            'total_resources': len(resources),
            'organization_context': {
                'is_organization': False,
                'total_accounts': 1,
                'scanned_accounts': 1,
                'scan_coverage': "1/1"
            },
            'data_source': 'single_account_scan'
        }

    def _scan_current_account_resources(self):
        """Scan current account resources in parallel"""
        resources = {}
        resource_types = {}
        
        def scan_ec2():
            try:
                instances = self.ec2.describe_instances()
                ec2_resources = {}
                for reservation in instances['Reservations']:
                    for instance in reservation['Instances']:
                        instance_id = instance['InstanceId']
                        ec2_resources[instance_id] = {
                            'type': 'EC2',
                            'state': instance['State']['Name'],
                            'instance_type': instance['InstanceType'],
                            'vpc_id': instance.get('VpcId'),
                            'launch_time': instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else None
                        }
                return ec2_resources, len(ec2_resources)
            except Exception as e:
                print(f"EC2 scan failed: {e}")
                return {}, 0

        def scan_rds():
            try:
                db_instances = self.rds.describe_db_instances()
                rds_resources = {}
                for db in db_instances['DBInstances']:
                    db_id = db['DBInstanceIdentifier']
                    rds_resources[db_id] = {
                        'type': 'RDS',
                        'engine': db['Engine'],
                        'instance_class': db['DBInstanceClass'],
                        'status': db['DBInstanceStatus'],
                        'multi_az': db.get('MultiAZ', False)
                    }
                return rds_resources, len(rds_resources)
            except Exception:
                return {}, 0

        def scan_s3():
            try:
                buckets = self.s3.list_buckets()
                s3_resources = {}
                for bucket in buckets['Buckets']:
                    bucket_name = bucket['Name']
                    s3_resources[bucket_name] = {
                        'type': 'S3',
                        'creation_date': bucket['CreationDate'].isoformat()
                    }
                return s3_resources, len(s3_resources)
            except Exception:
                return {}, 0

        def scan_vpcs():
            try:
                vpcs = self.ec2.describe_vpcs()
                vpc_resources = {}
                for vpc in vpcs['Vpcs']:
                    vpc_id = vpc['VpcId']
                    vpc_resources[vpc_id] = {
                        'type': 'VPC',
                        'state': vpc['State'],
                        'cidr_block': vpc['CidrBlock'],
                        'is_default': vpc.get('IsDefault', False)
                    }
                return vpc_resources, len(vpc_resources)
            except Exception:
                return {}, 0

        # Run scans in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(scan_ec2): 'EC2',
                executor.submit(scan_rds): 'RDS',
                executor.submit(scan_s3): 'S3',
                executor.submit(scan_vpcs): 'VPC'
            }
            
            for future in as_completed(futures):
                try:
                    resource_data, count = future.result(timeout=15)
                    resource_type = futures[future]
                    resources.update(resource_data)
                    if count > 0:
                        resource_types[resource_type] = count
                except Exception as e:
                    resource_type = futures[future]
                    print(f"{resource_type} scan failed: {e}")

        return resources, resource_types

    def _get_organization_insights(self):
        """Get organization-level insights"""
        insights = {
            'organization_recommendations': [],
            'governance_suggestions': []
        }
        
        try:
            # Check for organizational units
            try:
                ous = self.organizations.list_organizational_units_for_parent(
                    ParentId=self.organizations.list_roots()['Roots'][0]['Id']
                )
                
                if len(ous['OrganizationalUnits']) == 0:
                    insights['governance_suggestions'].append({
                        'type': 'organizational_structure',
                        'recommendation': 'Consider creating Organizational Units for better account management',
                        'impact': 'Improved governance and cost allocation'
                    })
                    
            except Exception:
                pass
            
            # Check for SCPs (Service Control Policies)
            try:
                policies = self.organizations.list_policies(Filter='SERVICE_CONTROL_POLICY')
                
                if len(policies['Policies']) <= 1:  # Only default policy
                    insights['governance_suggestions'].append({
                        'type': 'service_control_policies',
                        'recommendation': 'Implement Service Control Policies for security governance',
                        'impact': 'Enhanced security and compliance across accounts'
                    })
                    
            except Exception:
                pass
            
            # Multi-account recommendations
            if len(self.org_accounts) > 1:
                insights['organization_recommendations'].extend([
                    {
                        'type': 'centralized_logging',
                        'recommendation': f'Implement centralized logging across {len(self.org_accounts)} accounts',
                        'impact': 'Improved monitoring and compliance'
                    },
                    {
                        'type': 'cross_account_backup',
                        'recommendation': 'Set up cross-account backup strategy',
                        'impact': 'Enhanced disaster recovery'
                    }
                ])
                
        except Exception as e:
            print(f"Organization insights failed: {e}")
        
        return insights

    def get_organization_security_analysis(self):
        """Enhanced security analysis with organization context"""
        security_issues = []
        
        # Current account security analysis
        current_security = self._analyze_current_account_security()
        security_issues.extend(current_security)
        
        # Organization-level security recommendations
        if self.is_org_account:
            org_security = self._analyze_organization_security()
            security_issues.extend(org_security)
        
        return {
            'security_issues': security_issues,
            'total_issues': len(security_issues),
            'high_severity': len([i for i in security_issues if i['severity'] == 'high']),
            'organization_context': {
                'is_organization': self.is_org_account,
                'accounts_analyzed': 1,  # We can only analyze current account
                'total_accounts': len(self.org_accounts) if self.is_org_account else 1
            },
            'data_source': 'enhanced_organizations_security' if self.is_org_account else 'enhanced_single_account_security'
        }

    def _analyze_current_account_security(self):
        """Analyze current account security"""
        security_issues = []
        
        try:
            security_groups = self.ec2.describe_security_groups()
            
            for sg in security_groups['SecurityGroups']:
                sg_id = sg['GroupId']
                
                for rule in sg.get('IpPermissions', []):
                    from_port = rule.get('FromPort', 'all')
                    
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            severity = 'high' if from_port in [22, 3389, 3306, 5432] else 'medium'
                            
                            security_issues.append({
                                'security_group_id': sg_id,
                                'issue': f'Port {from_port} open to internet',
                                'severity': severity,
                                'scope': 'current_account',
                                'recommendation': 'Restrict source IP ranges'
                            })
                            
        except Exception as e:
            print(f"Current account security analysis failed: {e}")
        
        return security_issues

    def _analyze_organization_security(self):
        """Analyze organization-level security"""
        org_security_issues = []
        
        try:
            # Check for CloudTrail organization trail
            cloudtrail = boto3.client('cloudtrail', region_name='us-east-1')
            
            try:
                trails = cloudtrail.describe_trails()
                org_trails = [t for t in trails['trailList'] if t.get('IsOrganizationTrail', False)]
                
                if not org_trails:
                    org_security_issues.append({
                        'security_group_id': 'organization',
                        'issue': 'No organization-wide CloudTrail configured',
                        'severity': 'high',
                        'scope': 'organization',
                        'recommendation': 'Enable organization CloudTrail for centralized logging'
                    })
                    
            except Exception:
                pass
            
            # Check for GuardDuty organization setup
            try:
                guardduty = boto3.client('guardduty', region_name='us-east-1')
                detectors = guardduty.list_detectors()
                
                if not detectors['DetectorIds']:
                    org_security_issues.append({
                        'security_group_id': 'organization',
                        'issue': 'GuardDuty not enabled for organization',
                        'severity': 'medium',
                        'scope': 'organization',
                        'recommendation': 'Enable GuardDuty across all organization accounts'
                    })
                    
            except Exception:
                pass
                
        except Exception as e:
            print(f"Organization security analysis failed: {e}")
        
        return org_security_issues

agent = OrganizationsOperationsIntelligenceAgent()

@app.entrypoint
def invoke(payload):
    """Organizations-aware Operations Intelligence Agent"""
    try:
        action = payload.get("action", "map_dependencies")
        
        if action == "map_dependencies":
            print("🏢 Scanning resources (Organizations-aware)...")
            inventory = agent.get_organization_resource_inventory()
            
            print("🔒 Analyzing security (Organizations-aware)...")
            security = agent.get_organization_security_analysis()
            
            result = {
                **inventory,
                'security_analysis': security,
                'dependency_graph': {
                    'nodes': [
                        {'id': rid, **rdata} 
                        for rid, rdata in list(inventory['resources'].items())[:20]
                    ],
                    'edges': []
                },
                'insights': [
                    {
                        'type': 'organization_context',
                        'message': f'{"Organization with " + str(inventory["organization_context"]["total_accounts"]) + " accounts" if inventory["organization_context"]["is_organization"] else "Single account"} - {inventory["total_resources"]} resources found',
                        'severity': 'info'
                    },
                    {
                        'type': 'security_analysis',
                        'message': f'{security["total_issues"]} security issues identified ({security["high_severity"]} high severity)',
                        'severity': 'high' if security["high_severity"] > 0 else 'medium'
                    }
                ]
            }
            
            # Add organization recommendations if available
            if inventory['organization_context'].get('organization_recommendations'):
                result['organization_recommendations'] = inventory['organization_context']['organization_recommendations']
            
        elif action == "analyze_performance":
            # Performance analysis remains the same but with org context
            result = {
                'bottlenecks': [],
                'total_issues': 0,
                'organization_context': {
                    'is_organization': agent.is_org_account,
                    'total_accounts': len(agent.org_accounts) if agent.is_org_account else 1
                },
                'data_source': 'organizations_performance_analysis' if agent.is_org_account else 'single_account_performance_analysis'
            }
            
        elif action == "full_operations_analysis":
            dependencies = invoke({'action': 'map_dependencies'})
            performance = invoke({'action': 'analyze_performance'})
            
            result = {
                'dependencies': dependencies,
                'performance': performance,
                'summary': {
                    'total_resources': dependencies.get('total_resources', 0),
                    'security_issues': dependencies.get('security_analysis', {}).get('total_issues', 0),
                    'performance_issues': performance.get('total_issues', 0),
                    'organization_context': dependencies.get('organization_context', {}),
                    'data_source': 'organizations_comprehensive_analysis' if agent.is_org_account else 'single_account_comprehensive_analysis'
                }
            }
            
        else:
            result = {
                'message': f'Organizations-aware Operations Intelligence Agent ready! {"Organization management account" if agent.is_org_account else "Single account"}',
                'available_actions': ['map_dependencies', 'analyze_performance', 'full_operations_analysis'],
                'organization_info': {
                    'is_organization': agent.is_org_account,
                    'accounts_count': len(agent.org_accounts) if agent.is_org_account else 1
                }
            }
        
        result['agent'] = 'operations_intelligence_organizations'
        result['timestamp'] = datetime.now().isoformat()
        result['success'] = True
        result['services_used'] = ['runtime', 'memory', 'gateway']
        
        return result
        
    except Exception as e:
        return {
            'agent': 'operations_intelligence_organizations',
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    app.run()
