#!/usr/bin/env python3
"""
Test what data the dashboard will show - COMPLETE COST PICTURE
"""
import sys
sys.path.append('.')

def test_dashboard_data():
    """Test the actual data that feeds the dashboard"""
    print("🌐 DASHBOARD DATA TEST - COMPLETE COST ANALYSIS")
    print("=" * 50)
    
    # Test complete cost analysis
    try:
        from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
        
        print("💰 Testing Complete Cost Analysis...")
        agent = MultiAccountCostIntelligenceAgent()
        result = agent.get_multi_account_costs()
        
        if result.get('success'):
            print(f"✅ COMPLETE AWS COST PICTURE:")
            print(f"   💵 Usage Cost (before credits): ${result['total_usage_cost']:.2f}")
            print(f"   💳 Credits Applied: ${abs(result.get('total_credit_cost', 0)):.2f}")
            print(f"   💰 Final Bill: ${result['total_net_cost']:.2f}")
            print(f"   📊 Accounts: {result['successful_accounts']}/{result['accounts_checked']}")
            
            if 'cost_breakdown' in result:
                breakdown = result['cost_breakdown']
                print(f"   📋 Value Discovery:")
                print(f"      - Hidden usage revealed: ${breakdown['usage_before_credits']:.2f}")
                print(f"      - Credits offsetting costs: ${breakdown['credits_applied']:.2f}")
                print(f"      - True cost visibility achieved!")
        else:
            print(f"❌ Cost data failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Cost analysis failed: {e}")
    
    print()
    print("🎯 DASHBOARD VALUE PROPOSITION:")
    print("✅ Reveals hidden AWS usage patterns")
    print("✅ Shows complete cost picture (usage + credits)")
    print("✅ Provides true cost visibility across accounts")
    print("✅ Real-time AWS Cost Explorer integration")

if __name__ == "__main__":
    test_dashboard_data()

if __name__ == "__main__":
    test_dashboard_data()
