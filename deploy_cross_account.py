#!/usr/bin/env python3
"""
Deploy cross-account roles using CloudFormation
"""
import boto3
import json
import time

def deploy_to_account(account_id, account_name, template_body):
    """Deploy CloudFormation template to specific account"""
    print(f"🚀 Deploying to {account_name} ({account_id})...")
    
    try:
        # For demo purposes, we'll show the AWS CLI commands needed
        # In production, you'd use cross-account deployment or AWS Organizations
        
        print(f"   📋 AWS CLI commands for {account_name}:")
        print(f"   aws cloudformation create-stack \\")
        print(f"     --stack-name aws-operations-command-center-role \\")
        print(f"     --template-body file://cross-account-role-template.json \\")
        print(f"     --capabilities CAPABILITY_NAMED_IAM \\")
        print(f"     --profile {account_name.lower()}")
        print()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Deployment failed: {e}")
        return False

def main():
    """Deploy cross-account roles to all member accounts"""
    print("🚀 AWS Operations Command Center - Cross-Account Role Deployment")
    print("=" * 70)
    
    # Load template
    with open('cross-account-role-template.json', 'r') as f:
        template_body = f.read()
    
    # Target accounts (from our organization scan)
    accounts = [
        {'id': '592867232820', 'name': 'achamin'},
        {'id': '888577033943', 'name': 'crummyfun'}
    ]
    
    print("📋 Deployment Instructions:")
    print("=" * 30)
    
    for account in accounts:
        deploy_to_account(account['id'], account['name'], template_body)
    
    print("🎯 Alternative: Use AWS Organizations StackSets")
    print("=" * 50)
    print("aws cloudformation create-stack-set \\")
    print("  --stack-set-name aws-operations-command-center-roles \\")
    print("  --template-body file://cross-account-role-template.json \\")
    print("  --capabilities CAPABILITY_NAMED_IAM")
    print()
    print("aws cloudformation create-stack-instances \\")
    print("  --stack-set-name aws-operations-command-center-roles \\")
    print("  --accounts 592867232820 888577033943 \\")
    print("  --regions us-east-1")
    
    print("\n✅ After deployment, test with: python test_cross_account.py")

if __name__ == "__main__":
    main()
