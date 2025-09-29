#!/usr/bin/env python3
"""
Test cross-account access for organization overview
"""
import sys
sys.path.append('.')
import boto3
from agent.operations_intelligence_agent import OrganizationsOperationsIntelligenceAgent

def test_cross_account_access():
    """Test cross-account role assumption"""
    print("🔍 Testing Cross-Account Access")
    print("=" * 40)
    
    try:
        # Initialize agent
        agent = OrganizationsOperationsIntelligenceAgent()
        
        if not agent.is_org_account:
            print("❌ Not running in organization management account")
            return False
        
        print(f"✅ Organization detected: {len(agent.org_accounts)} accounts")
        
        # Test cross-account access for each account
        successful_accounts = 0
        
        for account in agent.org_accounts:
            account_id = account['id']
            account_name = account['name']
            
            print(f"\n🧪 Testing {account_name} ({account_id})...")
            
            try:
                # Try to assume role
                sts = boto3.client('sts')
                role_arn = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
                
                assumed_role = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=f"ops-test-{account_id}",
                    ExternalId="aws-operations-command-center"
                )
                
                # Test EC2 access with assumed role
                credentials = assumed_role['Credentials']
                ec2 = boto3.client(
                    'ec2',
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
                
                instances = ec2.describe_instances()
                instance_count = sum(
                    len(reservation['Instances']) 
                    for reservation in instances['Reservations']
                )
                
                print(f"   ✅ Access successful - {instance_count} EC2 instances found")
                successful_accounts += 1
                
            except Exception as e:
                if "AccessDenied" in str(e):
                    print(f"   ❌ Access denied - role not set up")
                else:
                    print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Cross-Account Access Summary:")
        print(f"   ✅ Successful: {successful_accounts}/{len(agent.org_accounts)} accounts")
        print(f"   📈 Coverage: {(successful_accounts/len(agent.org_accounts)*100):.1f}%")
        
        if successful_accounts == len(agent.org_accounts):
            print(f"\n🎉 Full organization access achieved!")
            return True
        else:
            print(f"\n⚠️  Partial access - set up roles in remaining accounts")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_full_organization_scan():
    """Test complete organization resource scan"""
    if not test_cross_account_access():
        print("\n⚠️  Skipping full scan - fix cross-account access first")
        return
    
    print(f"\n🌐 Testing Full Organization Scan")
    print("=" * 40)
    
    try:
        agent = OrganizationsOperationsIntelligenceAgent()
        result = agent.get_organization_resource_inventory()
        
        print(f"✅ Organization Scan Results:")
        print(f"   🏢 Organization: {result['organization_context']['is_organization']}")
        print(f"   📊 Total Resources: {result['total_resources']}")
        print(f"   🔧 Resource Types: {len(result['resource_types'])}")
        print(f"   📈 Account Coverage: {result['organization_context']['scan_coverage']}")
        
        if result['total_resources'] > 0:
            print(f"\n📋 Resource Breakdown:")
            for resource_type, count in list(result['resource_types'].items())[:5]:
                print(f"   - {resource_type}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full scan failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AWS Operations Command Center - Cross-Account Test")
    print("=" * 60)
    
    # Test cross-account access
    if test_cross_account_access():
        # Test full organization scan
        test_full_organization_scan()
    
    print(f"\n🎯 To set up missing roles, run: python setup_cross_account_roles.py")
