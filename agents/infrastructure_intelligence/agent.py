from bedrock_agentcore.runtime import BedrockAgentCoreApp
import boto3
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Template

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

app = BedrockAgentCoreApp()

class InfrastructureIntelligenceAgent:
    def __init__(self):
        self.ec2 = boto3.client('ec2', region_name='us-east-1')
        self.cloudformation = boto3.client('cloudformation', region_name='us-east-1')
        self.iam = boto3.client('iam', region_name='us-east-1')
        
        # Architecture templates
        self.templates = {
            'web_app_3tier': self._get_3tier_template(),
            'serverless_api': self._get_serverless_template(),
            'microservices': self._get_microservices_template(),
            'data_pipeline': self._get_data_pipeline_template()
        }
    
    def _get_3tier_template(self):
        """Production-ready 3-tier web application template"""
        return """
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Production-ready 3-tier web application'

Parameters:
  Environment:
    Type: String
    Default: prod
    AllowedValues: [dev, staging, prod]
  
  InstanceType:
    Type: String
    Default: {{ instance_type }}
    Description: EC2 instance type for web servers

Resources:
  # VPC with public and private subnets
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-vpc'

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-igw'

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Public Subnets for Load Balancer
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  # Private Subnets for Application Servers
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.3.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.4.0/24
      AvailabilityZone: !Select [1, !GetAZs '']

  # Database Subnets
  DBSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.5.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  DBSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.6.0/24
      AvailabilityZone: !Select [1, !GetAZs '']

  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${Environment}-alb'
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup

  # Auto Scaling Group for Web Servers
  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      VPCZoneIdentifier:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: 2
      MaxSize: 10
      DesiredCapacity: {{ desired_capacity }}
      TargetGroupARNs:
        - !Ref TargetGroup

  # RDS Database (Multi-AZ for production)
  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub '${Environment}-database'
      DBInstanceClass: {{ db_instance_class }}
      Engine: {{ db_engine }}
      MasterUsername: admin
      MasterUserPassword: !Ref DBPassword
      AllocatedStorage: {{ db_storage }}
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref DBSubnetGroup
      MultiAZ: {{ multi_az }}
      BackupRetentionPeriod: 7
      DeletionProtection: {{ deletion_protection }}

  # Security Groups with least privilege
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Application Load Balancer
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the load balancer
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub '${Environment}-alb-dns'

  DatabaseEndpoint:
    Description: RDS instance endpoint
    Value: !GetAtt Database.Endpoint.Address
    Export:
      Name: !Sub '${Environment}-db-endpoint'
"""

    def _get_serverless_template(self):
        """Serverless API template"""
        return """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: 'Serverless API with Lambda and API Gateway'

Parameters:
  Environment:
    Type: String
    Default: prod

Resources:
  # API Gateway
  ApiGateway:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Cors:
        AllowMethods: "'*'"
        AllowHeaders: "'*'"
        AllowOrigin: "'*'"

  # Lambda Function
  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.lambda_handler
      Runtime: python3.9
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /{proxy+}
            Method: ANY

  # DynamoDB Table
  DataTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${Environment}-data'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH

Outputs:
  ApiUrl:
    Description: API Gateway endpoint URL
    Value: !Sub 'https://${ApiGateway}.execute-api.${AWS::Region}.amazonaws.com/${Environment}'
"""

    def _get_microservices_template(self):
        """Microservices architecture template"""
        return """
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Microservices architecture with ECS Fargate'

Resources:
  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: microservices-cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  # Service Discovery Namespace
  ServiceDiscoveryNamespace:
    Type: AWS::ServiceDiscovery::PrivateDnsNamespace
    Properties:
      Name: microservices.local
      Vpc: !Ref VPC

  # Application Load Balancer for external traffic
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
"""

    def _get_data_pipeline_template(self):
        """Data pipeline template"""
        return """
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Data pipeline with S3, Lambda, and analytics'

Resources:
  # S3 Bucket for data storage
  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-data-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # Lambda for data processing
  DataProcessor:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-processor'
      Runtime: python3.9
      Handler: index.lambda_handler
      Code:
        ZipFile: |
          import json
          def lambda_handler(event, context):
              return {'statusCode': 200, 'body': json.dumps('Data processed')}
"""

    def generate_architecture(self, requirements: Dict[str, Any]):
        """Generate intelligent architecture based on requirements"""
        try:
            architecture_type = requirements.get('type', 'web_app_3tier')
            environment = requirements.get('environment', 'prod')
            scale = requirements.get('scale', 'medium')
            
            # Intelligent parameter selection based on requirements
            params = self._select_intelligent_parameters(requirements, scale, environment)
            
            # Get appropriate template
            template_content = self.templates.get(architecture_type, self.templates['web_app_3tier'])
            
            # Render template with intelligent parameters
            template = Template(template_content)
            rendered_template = template.render(**params)
            
            # Analyze the generated architecture
            analysis = self._analyze_architecture(architecture_type, params)
            
            return {
                'cloudformation_template': rendered_template,
                'parameters': params,
                'analysis': analysis,
                'estimated_monthly_cost': self._estimate_cost(architecture_type, params),
                'security_score': self._calculate_security_score(architecture_type),
                'reliability_score': self._calculate_reliability_score(architecture_type, params)
            }
            
        except Exception as e:
            return {'error': f"Architecture generation failed: {str(e)}"}
    
    def _select_intelligent_parameters(self, requirements: Dict[str, Any], scale: str, environment: str):
        """Intelligently select parameters based on requirements"""
        params = {}
        
        # Instance sizing based on scale and environment
        if scale == 'small':
            params['instance_type'] = 't3.small' if environment == 'prod' else 't3.micro'
            params['desired_capacity'] = 2
            params['db_instance_class'] = 'db.t3.micro'
        elif scale == 'large':
            params['instance_type'] = 'c5.xlarge'
            params['desired_capacity'] = 6
            params['db_instance_class'] = 'db.r5.large'
        else:  # medium
            params['instance_type'] = 't3.medium'
            params['desired_capacity'] = 3
            params['db_instance_class'] = 'db.t3.small'
        
        # Database configuration
        params['db_engine'] = requirements.get('database', 'mysql')
        params['db_storage'] = 100 if scale == 'large' else 50 if scale == 'medium' else 20
        
        # Production vs non-production settings
        if environment == 'prod':
            params['multi_az'] = 'true'
            params['deletion_protection'] = 'true'
        else:
            params['multi_az'] = 'false'
            params['deletion_protection'] = 'false'
        
        return params
    
    def _analyze_architecture(self, architecture_type: str, params: Dict[str, Any]):
        """Analyze the generated architecture for best practices"""
        analysis = {
            'strengths': [],
            'recommendations': [],
            'potential_issues': []
        }
        
        if architecture_type == 'web_app_3tier':
            analysis['strengths'].extend([
                'Multi-AZ deployment for high availability',
                'Auto Scaling for elasticity',
                'Load balancer for traffic distribution',
                'Private subnets for security'
            ])
            
            if params.get('multi_az') == 'true':
                analysis['strengths'].append('Database Multi-AZ for disaster recovery')
            else:
                analysis['recommendations'].append('Enable Multi-AZ for production database')
            
            if params.get('instance_type', '').startswith('t3'):
                analysis['recommendations'].append('Consider compute-optimized instances for CPU-intensive workloads')
        
        return analysis
    
    def _estimate_cost(self, architecture_type: str, params: Dict[str, Any]) -> float:
        """Estimate monthly cost for the architecture"""
        cost = 0
        
        if architecture_type == 'web_app_3tier':
            # EC2 instances (simplified pricing)
            instance_type = params.get('instance_type', 't3.medium')
            capacity = params.get('desired_capacity', 3)
            
            instance_costs = {
                't3.micro': 8.5, 't3.small': 17, 't3.medium': 34,
                'c5.large': 73, 'c5.xlarge': 146
            }
            
            cost += instance_costs.get(instance_type, 34) * capacity
            
            # RDS cost
            db_class = params.get('db_instance_class', 'db.t3.small')
            db_costs = {
                'db.t3.micro': 15, 'db.t3.small': 30, 'db.r5.large': 180
            }
            cost += db_costs.get(db_class, 30)
            
            # Load balancer
            cost += 23  # ALB cost
            
            # Storage and data transfer (estimated)
            cost += 50
        
        elif architecture_type == 'serverless_api':
            # Lambda + API Gateway + DynamoDB (estimated for medium usage)
            cost += 25
        
        return round(cost, 2)
    
    def _calculate_security_score(self, architecture_type: str) -> int:
        """Calculate security score out of 100"""
        base_scores = {
            'web_app_3tier': 85,  # Good security with VPC, security groups
            'serverless_api': 90,  # Serverless has good built-in security
            'microservices': 80,   # More complex, more attack surface
            'data_pipeline': 75    # Depends on data sensitivity
        }
        return base_scores.get(architecture_type, 75)
    
    def _calculate_reliability_score(self, architecture_type: str, params: Dict[str, Any]) -> int:
        """Calculate reliability score out of 100"""
        base_score = 70
        
        if architecture_type == 'web_app_3tier':
            base_score = 80
            if params.get('multi_az') == 'true':
                base_score += 10
            if params.get('desired_capacity', 1) >= 2:
                base_score += 5
        
        elif architecture_type == 'serverless_api':
            base_score = 95  # Serverless is highly reliable
        
        return min(base_score, 100)

    def assess_existing_infrastructure(self):
        """Assess existing AWS infrastructure for improvements"""
        try:
            assessment = {
                'vpc_analysis': [],
                'security_issues': [],
                'reliability_concerns': [],
                'recommendations': []
            }
            
            # Analyze VPCs
            vpcs = self.ec2.describe_vpcs()
            for vpc in vpcs['Vpcs']:
                vpc_id = vpc['VpcId']
                
                # Check if VPC has both public and private subnets
                subnets = self.ec2.describe_subnets(
                    Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
                )
                
                public_subnets = 0
                private_subnets = 0
                
                for subnet in subnets['Subnets']:
                    if subnet.get('MapPublicIpOnLaunch', False):
                        public_subnets += 1
                    else:
                        private_subnets += 1
                
                assessment['vpc_analysis'].append({
                    'vpc_id': vpc_id,
                    'public_subnets': public_subnets,
                    'private_subnets': private_subnets,
                    'recommendation': 'Good architecture' if public_subnets > 0 and private_subnets > 0 
                                    else 'Consider adding private subnets for better security'
                })
            
            # Check for security groups with overly permissive rules
            security_groups = self.ec2.describe_security_groups()
            for sg in security_groups['SecurityGroups']:
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            assessment['security_issues'].append({
                                'security_group_id': sg['GroupId'],
                                'issue': f"Port {rule.get('FromPort', 'all')} open to 0.0.0.0/0",
                                'severity': 'high' if rule.get('FromPort') == 22 else 'medium',
                                'recommendation': 'Restrict source IP ranges'
                            })
            
            return assessment
            
        except Exception as e:
            return {'error': f"Infrastructure assessment failed: {str(e)}"}

infrastructure_agent = InfrastructureIntelligenceAgent()

@app.entrypoint
def invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Infrastructure Intelligence Agent - Smart AWS architecture generation"""
    try:
        action = payload.get("action", "generate")
        
        if action == "generate_architecture":
            requirements = payload.get("requirements", {})
            result = infrastructure_agent.generate_architecture(requirements)
            
        elif action == "assess_existing":
            result = infrastructure_agent.assess_existing_infrastructure()
            
        else:
            result = {
                'message': 'Infrastructure Intelligence Agent ready. Available actions: generate_architecture, assess_existing'
            }
        
        result['agent'] = 'infrastructure_intelligence'
        result['timestamp'] = datetime.now().isoformat()
        result['success'] = True
        
        return result
        
    except Exception as e:
        return {
            'agent': 'infrastructure_intelligence',
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    app.run()
