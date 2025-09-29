#!/usr/bin/env python3
"""
Deploy cross-account roles using configured AWS profiles
"""
import boto3
import json

def deploy_role_to_profile(profile_name, account_name):
    """Deploy role using specific AWS profile"""
    print(f"🚀 Deploying to {account_name} using profile '{profile_name}'...")
    
    try:
        # Create session with specific profile and region
        session = boto3.Session(profile_name=profile_name, region_name='us-east-1')
        cf = session.client('cloudformation')
        
        # Load template
        with open('cross-account-role-template.json', 'r') as f:
            template_body = f.read()
        
        # Deploy stack
        response = cf.create_stack(
            StackName='aws-operations-command-center-role',
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        
        print(f"   ✅ Stack created: {response['StackId']}")
        
        # Wait for completion
        print(f"   ⏳ Waiting for stack creation...")
        waiter = cf.get_waiter('stack_create_complete')
        waiter.wait(StackName='aws-operations-command-center-role')
        
        print(f"   ✅ {account_name} deployment completed!")
        return True
        
    except Exception as e:
        if 'AlreadyExistsException' in str(e):
            print(f"   ⚠️  Stack already exists in {account_name}")
            return True
        else:
            print(f"   ❌ Deployment failed: {e}")
            return False

def main():
    """Deploy to all accounts using configured profiles"""
    print("🚀 AWS Operations Command Center - Profile-Based Deployment")
    print("=" * 60)
    
    # Profile mappings
    deployments = [
        {'profile': 'simi-ops', 'account': 'crummyfun'},
        {'profile': 'achamin', 'account': 'achamin'}
    ]
    
    successful = 0
    
    for deployment in deployments:
        if deploy_role_to_profile(deployment['profile'], deployment['account']):
            successful += 1
        print()
    
    print(f"📊 Deployment Summary:")
    print(f"   ✅ Successful: {successful}/{len(deployments)} accounts")
    print(f"   🏢 Management account: Already configured")
    print(f"   📈 Total coverage: {successful + 1}/3 accounts")
    
    if successful == len(deployments):
        print(f"\n🎉 Full organization access achieved!")
        print(f"🧪 Test with: python test_cross_account.py")
    else:
        print(f"\n⚠️  Some deployments failed - check AWS credentials")

if __name__ == "__main__":
    main()
