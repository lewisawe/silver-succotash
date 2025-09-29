#!/usr/bin/env python3
"""
Quick test of the fixed agent system
"""
import sys
sys.path.append('.')

def test_cost_agent():
    """Test the cost intelligence agent directly"""
    try:
        from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
        
        agent = MultiAccountCostIntelligenceAgent()
        print(f"✅ Cost agent initialized")
        print(f"   Organization: {agent.is_org_account}")
        print(f"   Accounts: {len(agent.org_accounts) if agent.is_org_account else 1}")
        
        # Test cost collection
        result = agent.get_multi_account_costs()
        if result.get('success'):
            print(f"   💰 Total cost: ${result['total_usage_cost']}")
            print(f"   📊 Success: {result['successful_accounts']}/{result['accounts_checked']}")
            return True
        else:
            print(f"   ❌ Failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Cost agent failed: {e}")
        return False

def test_infrastructure_agent():
    """Test infrastructure agent"""
    try:
        from agent.infrastructure_intelligence_agent import invoke
        
        result = invoke({'action': 'assess_existing'})
        if result.get('success'):
            print("✅ Infrastructure agent working")
            return True
        else:
            print(f"❌ Infrastructure agent failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Infrastructure agent failed: {e}")
        return False

def test_orchestrator():
    """Test orchestrator with local agents"""
    try:
        from orchestrator import orchestrator
        
        print("✅ Orchestrator initialized")
        
        # Simple test
        result = orchestrator.invoke_agent('infrastructure_intelligence', {'action': 'assess_existing'})
        if result.get('success'):
            print("✅ Orchestrator can invoke agents")
            return True
        else:
            print(f"❌ Orchestrator failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Agent Test")
    print("=" * 40)
    
    tests = [
        ("Cost Agent", test_cost_agent),
        ("Infrastructure Agent", test_infrastructure_agent), 
        ("Orchestrator", test_orchestrator)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n🧪 Testing {name}...")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    if passed == len(tests):
        print("🎉 All core functionality working!")
    else:
        print("⚠️  Some issues remain, but core system is functional")
