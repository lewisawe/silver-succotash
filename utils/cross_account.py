"""
Cross-account utilities for Organizations
"""
import boto3
import json
from utils.error_handling import safe_aws_call
from utils.logging_config import api_logger

def ensure_cross_account_role(account_id: str, role_name: str = "OrganizationAccountAccessRole"):
    """Ensure cross-account role exists for scanning"""
    try:
        iam = boto3.client('iam')
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:root"
                },
                "Action": "sts:AssumeRole"
            }]
        }
        
        # Try to create role (will fail if exists, which is fine)
        safe_aws_call(
            iam.create_role,
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Cross-account access for AWS Operations Command Center"
        )
        
        # Attach read-only policy
        safe_aws_call(
            iam.attach_role_policy,
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/ReadOnlyAccess"
        )
        
        return True
        
    except Exception as e:
        api_logger.error(f"Failed to ensure cross-account role: {e}")
        return False
