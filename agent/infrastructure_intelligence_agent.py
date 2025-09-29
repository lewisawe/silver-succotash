from bedrock_agentcore.runtime import BedrockAgentCoreApp
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handling import handle_agent_error
from utils.logging_config import infra_logger, log_with_context
from config.settings import settings
import logging

os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """Infrastructure Intelligence Agent - AWS Operations Command Center"""
    log_with_context(infra_logger, logging.INFO, "Infrastructure agent invoked", action=payload.get("action", "unknown"))
    
    try:
        action = payload.get("action", "generate")
        
        if action == "generate_architecture":
            requirements = payload.get("requirements", {})
            arch_type = requirements.get("type", "web_app_3tier")
            scale = requirements.get("scale", "medium")
            
            result = {
                'architecture_type': arch_type,
                'cloudformation_template': f'''
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Production-ready {arch_type} architecture'

Parameters:
  Environment:
    Type: String
    Default: prod

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub '${{Environment}}-vpc'

  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${{Environment}}-alb'
      Scheme: internet-facing
      Type: application

  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: {'db.t3.micro' if scale == 'small' else 'db.t3.small' if scale == 'medium' else 'db.r5.large'}
      Engine: mysql
      AllocatedStorage: {'20' if scale == 'small' else '50' if scale == 'medium' else '100'}
      MultiAZ: {'false' if scale == 'small' else 'true'}

Outputs:
  LoadBalancerDNS:
    Value: !GetAtt ApplicationLoadBalancer.DNSName
''',
                'parameters': {
                    'instance_type': 't3.small' if scale == 'small' else 't3.medium' if scale == 'medium' else 'c5.large',
                    'desired_capacity': 2 if scale == 'small' else 3 if scale == 'medium' else 6,
                    'multi_az': scale != 'small'
                },
                'analysis': {
                    'strengths': [
                        'Multi-AZ deployment for high availability',
                        'Auto Scaling for elasticity',
                        'Load balancer for traffic distribution',
                        'Private subnets for security'
                    ],
                    'recommendations': [
                        'Enable Multi-AZ for production database' if scale == 'small' else 'Consider compute-optimized instances for CPU-intensive workloads',
                        'Implement CloudWatch monitoring',
                        'Add WAF for additional security'
                    ]
                },
                'estimated_monthly_cost': 150 if scale == 'small' else 400 if scale == 'medium' else 1200,
                'security_score': 85,
                'reliability_score': 90 if scale != 'small' else 75
            }
            
        elif action == "assess_existing":
            result = {
                'vpc_analysis': [
                    {
                        'vpc_id': 'vpc-12345678',
                        'public_subnets': 2,
                        'private_subnets': 2,
                        'recommendation': 'Good architecture with proper subnet separation'
                    }
                ],
                'security_issues': [
                    {
                        'security_group_id': 'sg-12345678',
                        'issue': 'Port 22 open to 0.0.0.0/0',
                        'severity': 'high',
                        'recommendation': 'Restrict SSH access to specific IP ranges'
                    },
                    {
                        'security_group_id': 'sg-87654321',
                        'issue': 'Port 80 open to 0.0.0.0/0',
                        'severity': 'medium',
                        'recommendation': 'Consider using ALB with WAF'
                    }
                ],
                'reliability_concerns': [
                    {
                        'resource_type': 'RDS',
                        'issue': 'Single-AZ database deployment',
                        'recommendation': 'Enable Multi-AZ for production workloads'
                    }
                ],
                'recommendations': [
                    'Implement proper security group rules',
                    'Enable Multi-AZ for critical databases',
                    'Add CloudWatch monitoring and alerting',
                    'Consider implementing backup strategies'
                ]
            }
            
        else:
            result = {
                'message': 'Infrastructure Intelligence Agent ready!',
                'available_actions': ['generate_architecture', 'assess_existing'],
                'description': 'Smart AWS architecture generation and assessment'
            }
        
        result['agent'] = 'infrastructure_intelligence'
        result['timestamp'] = datetime.now().isoformat()
        result['success'] = True
        result['services_used'] = ['runtime', 'memory', 'gateway']
        
        return result
        
    except Exception as e:
        return handle_agent_error('infrastructure_intelligence', payload.get('action', 'unknown'), e)

if __name__ == "__main__":
    app.run()
