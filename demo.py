#!/usr/bin/env python3
"""
Live Demo Script for AWS Operations Command Center
"""
import sys
sys.path.append('.')
import json
from datetime import datetime

def demo_agent_discovery():
    """Demo 1: Self-Discovering Agents"""
    print("🔍 DEMO 1: Self-Discovering Multi-Agent System")
    print("=" * 50)
    
    from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
    
    agent = MultiAccountCostIntelligenceAgent()
    print(f"✅ Agent auto-discovered environment:")
    print(f"   🏢 Organization Account: {agent.is_org_account}")
    print(f"   📊 Accounts Detected: {len(agent.org_accounts)}")
    print(f"   🆔 Current Account: {agent.current_account_id}")
    
    if agent.is_org_account:
        print(f"   📋 Organization Accounts:")
        for acc in agent.org_accounts[:3]:  # Show first 3
            print(f"      - {acc['name']} ({acc['id']})")
    print()

def demo_real_cost_analysis():
    """Demo 2: Real AWS Cost Analysis"""
    print("💰 DEMO 2: Real Multi-Account Cost Analysis")
    print("=" * 50)
    
    from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
    
    agent = MultiAccountCostIntelligenceAgent()
    result = agent.get_multi_account_costs()
    
    if result.get('success'):
        print(f"✅ Live AWS Cost Data Retrieved:")
        print(f"   💵 Total Usage Cost: ${result['total_usage_cost']}")
        print(f"   📊 Accounts Analyzed: {result['successful_accounts']}/{result['accounts_checked']}")
        
        if result.get('accounts'):
            print(f"   📋 Per-Account Breakdown:")
            for acc in result['accounts'][:3]:
                print(f"      - Account {acc['account_id']}: ${acc['cost']}")
    else:
        print(f"❌ Cost analysis failed: {result.get('error')}")
    print()

def demo_agent_coordination():
    """Demo 3: Multi-Agent Orchestration"""
    print("🤝 DEMO 3: Multi-Agent Orchestration")
    print("=" * 50)
    
    from orchestrator import orchestrator
    
    print("🎯 Orchestrating 3 specialized agents...")
    
    # Test individual agents
    agents = [
        ("Cost Intelligence", "cost_intelligence"),
        ("Infrastructure Intelligence", "infrastructure_intelligence"),
        ("Operations Intelligence", "operations_intelligence")
    ]
    
    working_agents = 0
    for name, agent_id in agents:
        try:
            result = orchestrator.invoke_agent(agent_id, {'action': 'test'})
            if result.get('success', True):  # Some agents don't return success flag
                print(f"   ✅ {name} Agent: READY")
                working_agents += 1
            else:
                print(f"   ⚠️  {name} Agent: {result.get('error', 'Issue detected')}")
        except Exception as e:
            print(f"   ❌ {name} Agent: {str(e)}")
    
    print(f"\n🎯 Agent Coordination: {working_agents}/3 agents operational")
    print()

def demo_memory_service():
    """Demo 4: Cross-Agent Memory"""
    print("🧠 DEMO 4: Cross-Agent Memory Service")
    print("=" * 50)
    
    from utils.memory_service import memory_service
    import uuid
    
    session_id = str(uuid.uuid4())[:8]
    
    # Store context
    context = {
        'user_request': 'Analyze my AWS costs',
        'timestamp': datetime.now().isoformat(),
        'agent_chain': ['cost_intelligence', 'operations_intelligence']
    }
    
    success = memory_service.store_context(session_id, context)
    print(f"✅ Context stored in memory service: {success}")
    
    # Retrieve context
    retrieved = memory_service.get_context(session_id)
    if retrieved:
        print(f"✅ Context retrieved successfully")
        print(f"   📝 Session: {session_id}")
        print(f"   🔗 Agent Chain: {retrieved['agent_chain']}")
    print()

def demo_architecture_generation():
    """Demo 5: AI Architecture Generation"""
    print("🏗️ DEMO 5: AI-Powered Architecture Generation")
    print("=" * 50)
    
    from agent.infrastructure_intelligence_agent import invoke
    
    result = invoke({
        'action': 'generate_architecture',
        'requirements': {
            'type': 'web_app_3tier',
            'scale': 'small'
        }
    })
    
    if result.get('success'):
        print("✅ Architecture Generated:")
        print(f"   🏛️  Type: {result.get('architecture_type', 'N/A')}")
        print(f"   💰 Estimated Cost: ${result.get('estimated_monthly_cost', 'N/A')}/month")
        print(f"   🔒 Security Score: {result.get('security_score', 'N/A')}/100")
        print(f"   ⚡ Performance Score: {result.get('performance_score', 'N/A')}/100")
    else:
        print(f"❌ Architecture generation failed: {result.get('error')}")
    print()

def main():
    """Run complete demo"""
    print("🚀 AWS OPERATIONS COMMAND CENTER - LIVE DEMO")
    print("=" * 60)
    print("Demonstrating Advanced Multi-Agent AI System with AgentCore")
    print("=" * 60)
    print()
    
    demos = [
        demo_agent_discovery,
        demo_real_cost_analysis,
        demo_agent_coordination,
        demo_memory_service,
        demo_architecture_generation
    ]
    
    for i, demo_func in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"❌ Demo {i} failed: {e}")
            print()
    
    print("🎯 DEMO COMPLETE")
    print("=" * 60)
    print("Key Features Demonstrated:")
    print("✅ Self-discovering multi-agent system")
    print("✅ Real AWS API integration")
    print("✅ Cross-agent orchestration")
    print("✅ Memory service for context sharing")
    print("✅ AI-powered architecture generation")
    print("✅ Production-ready error handling")

if __name__ == "__main__":
    main()
