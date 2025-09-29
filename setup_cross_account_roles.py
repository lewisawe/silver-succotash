#!/usr/bin/env python3
"""
Setup cross-account IAM roles for full organization access
"""
import boto3
import json
import sys

def create_cross_account_role(management_account_id, target_account_id=None):
    """Create OrganizationAccountAccessRole in target account"""
    
    # Trust policy allowing management account to assume role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{management_account_id}:root"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "sts:ExternalId": "aws-operations-command-center"
                    }
                }
            }
        ]
    }
    
    # Permissions policy for read-only access
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:Describe*",
                    "rds:Describe*",
                    "s3:ListAllMyBuckets",
                    "s3:GetBucketLocation",
                    "elbv2:Describe*",
                    "cloudwatch:GetMetricStatistics",
                    "ce:GetCostAndUsage",
                    "ce:GetUsageReport",
                    "organizations:ListAccounts",
                    "organizations:DescribeOrganization"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        iam = boto3.client('iam')
        
        # Create role
        role_response = iam.create_role(
            RoleName='OrganizationAccountAccessRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Cross-account access for AWS Operations Command Center',
            MaxSessionDuration=3600
        )
        
        print(f"✅ Created role: {role_response['Role']['Arn']}")
        
        # Create and attach policy
        policy_response = iam.create_policy(
            PolicyName='AWSOperationsCommandCenterPolicy',
            PolicyDocument=json.dumps(permissions_policy),
            Description='Read-only access for AWS Operations Command Center'
        )
        
        iam.attach_role_policy(
            RoleName='OrganizationAccountAccessRole',
            PolicyArn=policy_response['Policy']['Arn']
        )
        
        print(f"✅ Attached policy: {policy_response['Policy']['Arn']}")
        
        return role_response['Role']['Arn']
        
    except Exception as e:
        if 'EntityAlreadyExists' in str(e):
            print(f"⚠️  Role already exists in this account")
            return f"arn:aws:iam::{target_account_id or 'current'}:role/OrganizationAccountAccessRole"
        else:
            print(f"❌ Failed to create role: {e}")
            return None

def setup_organization_roles():
    """Setup roles across all organization accounts"""
    try:
        # Get current account (should be management account)
        sts = boto3.client('sts')
        current_account = sts.get_caller_identity()['Account']
        print(f"🏢 Management Account: {current_account}")
        
        # Get organization accounts
        org = boto3.client('organizations')
        accounts = org.list_accounts()['Accounts']
        
        print(f"📊 Found {len(accounts)} accounts in organization")
        
        # Create role in management account (for self-access)
        print(f"\n🔧 Setting up management account role...")
        mgmt_role = create_cross_account_role(current_account, current_account)
        
        # For other accounts, provide CloudFormation template
        other_accounts = [acc for acc in accounts if acc['Id'] != current_account and acc['Status'] == 'ACTIVE']
        
        if other_accounts:
            print(f"\n📋 For the other {len(other_accounts)} accounts, deploy this CloudFormation template:")
            print("=" * 60)
            
            cf_template = {
                "AWSTemplateFormatVersion": "2010-09-09",
                "Description": "Cross-account role for AWS Operations Command Center",
                "Resources": {
                    "CrossAccountRole": {
                        "Type": "AWS::IAM::Role",
                        "Properties": {
                            "RoleName": "OrganizationAccountAccessRole",
                            "AssumeRolePolicyDocument": {
                                "Version": "2012-10-17",
                                "Statement": [{
                                    "Effect": "Allow",
                                    "Principal": {"AWS": f"arn:aws:iam::{current_account}:root"},
                                    "Action": "sts:AssumeRole",
                                    "Condition": {
                                        "StringEquals": {
                                            "sts:ExternalId": "aws-operations-command-center"
                                        }
                                    }
                                }]
                            },
                            "ManagedPolicyArns": [
                                "arn:aws:iam::aws:policy/ReadOnlyAccess"
                            ]
                        }
                    }
                }
            }
            
            print(json.dumps(cf_template, indent=2))
            print("=" * 60)
            
            print(f"\n📝 Deploy this template in accounts:")
            for acc in other_accounts:
                print(f"   - {acc['Name']} ({acc['Id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AWS Operations Command Center - Cross-Account Setup")
    print("=" * 60)
    
    if setup_organization_roles():
        print("\n✅ Setup completed!")
        print("\n🎯 Next steps:")
        print("1. Deploy CloudFormation template in member accounts")
        print("2. Test cross-account access with: python test_cross_account.py")
        print("3. Run full organization scan")
    else:
        print("\n❌ Setup failed - check permissions and try again")
