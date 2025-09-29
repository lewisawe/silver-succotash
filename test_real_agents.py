#!/usr/bin/env python3
"""
Real-world test script for all 3 agents with actual AWS APIs
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cost_intelligence_agent():
    """Test cost intelligence agent with real AWS APIs"""
    print("💰 Testing Cost Intelligence Agent...")
    
    try:
        from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
        
        agent = MultiAccountCostIntelligenceAgent()
        print(f"   ✅ Agent initialized (Organization: {agent.is_org_account})")
        print(f"   📊 Accounts detected: {len(agent.org_accounts) if agent.is_org_account else 1}")
        
        # Test multi-account cost collection
        print("   🔍 Collecting multi-account costs...")
        result = agent.get_multi_account_costs()
        
        if result.get('successful_accounts', 0) > 0:
            print(f"   ✅ Successfully collected costs from {result['successful_accounts']} accounts")
            print(f"   💵 Total usage cost: ${result['total_usage_cost']}")
            
            if result.get('accounts'):
                print(f"   📊 Accounts analyzed: {len(result['accounts'])}")
            
            return True, result
        else:
            print(f"   ⚠️  No accounts successfully processed")
            return False, result
            
    except Exception as e:
        print(f"   ❌ Cost agent test failed: {e}")
        return False, {'error': str(e)}

def test_operations_intelligence_agent():
    """Test operations intelligence agent with real AWS APIs"""
    print("\n🗺️ Testing Operations Intelligence Agent...")
    
    try:
        from agent.operations_intelligence_agent import OrganizationsOperationsIntelligenceAgent
        
        agent = OrganizationsOperationsIntelligenceAgent()
        print(f"   ✅ Agent initialized (Organization: {agent.is_org_account})")
        
        # Test resource inventory
        print("   🔍 Scanning resource inventory...")
        result = agent.get_organization_resource_inventory()
        
        total_resources = result.get('total_resources', 0)
        if total_resources > 0:
            print(f"   ✅ Found {total_resources} resources")
            
            resource_types = result.get('resource_types', {})
            for resource_type, count in resource_types.items():
                print(f"   📦 {resource_type}: {count}")
            
            org_context = result.get('organization_context', {})
            if org_context.get('is_organization'):
                print(f"   🏢 Organization with {org_context.get('total_accounts', 0)} accounts")
            
            return True, result
        else:
            print("   ⚠️  No resources found")
            return False, result
            
    except Exception as e:
        print(f"   ❌ Operations agent test failed: {e}")
        return False, {'error': str(e)}

def test_infrastructure_intelligence_agent():
    """Test infrastructure intelligence agent"""
    print("\n🏗️ Testing Infrastructure Intelligence Agent...")
    
    try:
        from agent.infrastructure_intelligence_agent import invoke
        
        # Test architecture assessment
        print("   🔍 Assessing existing infrastructure...")
        assess_payload = {"action": "assess_existing"}
        assess_result = invoke(assess_payload)
        
        if assess_result.get('success'):
            print("   ✅ Infrastructure assessment completed")
            if 'security_score' in assess_result:
                print(f"   🔒 Security score: {assess_result['security_score']}/100")
            if 'reliability_score' in assess_result:
                print(f"   🛡️  Reliability score: {assess_result['reliability_score']}/100")
        
        # Test architecture generation
        print("   🏗️ Generating sample architecture...")
        gen_payload = {
            "action": "generate_architecture",
            "requirements": {
                "type": "web_app_3tier",
                "scale": "small"
            }
        }
        gen_result = invoke(gen_payload)
        
        if gen_result.get('success'):
            print("   ✅ Architecture generation completed")
            if 'estimated_monthly_cost' in gen_result:
                print(f"   💰 Estimated cost: ${gen_result['estimated_monthly_cost']}/month")
            if 'architecture_type' in gen_result:
                print(f"   🏛️  Architecture: {gen_result['architecture_type']}")
            
            return True, {'assess': assess_result, 'generate': gen_result}
        else:
            return False, {'assess': assess_result, 'generate': gen_result}
            
    except Exception as e:
        print(f"   ❌ Infrastructure agent test failed: {e}")
        return False, {'error': str(e)}

def test_orchestrator():
    """Test orchestrator with real agents"""
    print("\n🎯 Testing Orchestrator...")
    
    try:
        from orchestrator import LocalAgentOrchestrator
        
        orchestrator = LocalAgentOrchestrator()
        print("   ✅ Orchestrator initialized")
        
        # Test full analysis
        print("   🔍 Running full analysis orchestration...")
        result = orchestrator.orchestrate_full_analysis()
        
        if result.get('success'):
            print("   ✅ Full analysis completed")
            
            # Check results from each agent
            if 'cost_analysis' in result['results']:
                cost_success = result['results']['cost_analysis'].get('success', False)
                print(f"   💰 Cost analysis: {'✅' if cost_success else '❌'}")
            
            if 'operations_analysis' in result['results']:
                ops_success = result['results']['operations_analysis'].get('success', False)
                print(f"   🗺️ Operations analysis: {'✅' if ops_success else '❌'}")
            
            if 'infrastructure_assessment' in result['results']:
                infra_success = result['results']['infrastructure_assessment'].get('success', False)
                print(f"   🏗️ Infrastructure assessment: {'✅' if infra_success else '❌'}")
            
            # Check coordinated recommendations
            recommendations = result.get('coordinated_recommendations', [])
            print(f"   🎯 Generated {len(recommendations)} coordinated recommendations")
            
            return True, result
        else:
            print(f"   ❌ Orchestration failed: {result.get('error', 'Unknown error')}")
            return False, result
            
    except Exception as e:
        print(f"   ❌ Orchestrator test failed: {e}")
        return False, {'error': str(e)}

def main():
    """Run all real-world tests"""
    print("🚀 AWS Operations Command Center - Real-World Agent Tests")
    print("=" * 70)
    print("Testing with actual AWS APIs and real data...")
    print()
    
    results = {}
    
    # Test each agent
    tests = [
        ("Cost Intelligence", test_cost_intelligence_agent),
        ("Operations Intelligence", test_operations_intelligence_agent),
        ("Infrastructure Intelligence", test_infrastructure_intelligence_agent),
        ("Orchestrator", test_orchestrator)
    ]
    
    for test_name, test_func in tests:
        try:
            success, data = test_func()
            results[test_name] = {'success': success, 'data': data}
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results[test_name] = {'success': False, 'error': str(e)}
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Real-World Test Results:")
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"   {test_name}: {status}")
        
        if not result['success'] and 'error' in result:
            print(f"      Error: {result['error']}")
    
    print(f"\nOverall: {passed}/{total} agents working ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All agents working perfectly with real AWS data!")
        print("\n💡 Your system is production-ready and handling real workloads!")
    elif passed > 0:
        print(f"\n⚠️  {passed} agents working, {total-passed} need attention")
        print("Check the error messages above for troubleshooting")
    else:
        print("\n❌ No agents working - check AWS credentials and permissions")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"real_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
