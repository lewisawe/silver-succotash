#!/usr/bin/env python3
"""
Demo script to show AWS Operations Command Center functionality
"""
import sys
import json
sys.path.append('.')

from agent.cost_intelligence_agent import invoke as cost_invoke
from agent.infrastructure_intelligence_agent import invoke as infra_invoke
from agent.operations_intelligence_agent import invoke as ops_invoke
from orchestrator import orchestrator

def print_banner():
    print("🚀 AWS Operations Command Center - Frontend Demo")
    print("=" * 60)
    print("Multi-Agent AWS Analysis & Optimization Platform")
    print("=" * 60)

def demo_cost_analysis():
    print("\n💰 COST INTELLIGENCE AGENT")
    print("-" * 40)
    result = cost_invoke({'action': 'full_analysis'})
    
    cost_data = result['cost_analysis']
    print(f"📊 Monthly Cost: ${cost_data['current_monthly_cost']}")
    print(f"📈 Trend: {cost_data['trend']}")
    print(f"🔍 Data Source: {cost_data['data_source']}")
    
    opt_data = result['optimizations']
    print(f"💡 Potential Savings: ${opt_data['total_potential_monthly_savings']}/month")
    print(f"🎯 Opportunities: {len(opt_data['opportunities'])}")
    
    print(f"🤖 Agent: {result['agent']} | Services: {', '.join(result['services_used'])}")

def demo_operations_analysis():
    print("\n🗺️ OPERATIONS INTELLIGENCE AGENT")
    print("-" * 40)
    result = ops_invoke({'action': 'map_dependencies'})
    
    print(f"📦 Total Resources: {result['total_resources']}")
    print(f"🏗️ Resource Types: {result['resource_types']}")
    print(f"🔍 Data Source: {result['data_source']}")
    
    if result.get('security_analysis'):
        security_issues = len(result['security_analysis'].get('security_issues', []))
        print(f"🔒 Security Issues: {security_issues}")
    
    print(f"🤖 Agent: {result['agent']} | Services: {', '.join(result['services_used'])}")

def demo_infrastructure_generation():
    print("\n🏗️ INFRASTRUCTURE INTELLIGENCE AGENT")
    print("-" * 40)
    result = infra_invoke({
        'action': 'generate_architecture',
        'requirements': {'type': 'web_app_3tier', 'scale': 'medium'}
    })
    
    print(f"🏛️ Architecture: {result['architecture_type']}")
    print(f"💰 Estimated Cost: ${result['estimated_monthly_cost']}/month")
    print(f"🔒 Security Score: {result['security_score']}/100")
    print(f"⚡ Reliability Score: {result['reliability_score']}/100")
    print(f"📋 Recommendations: {len(result['analysis']['recommendations'])}")
    
    print(f"🤖 Agent: {result['agent']} | Services: {', '.join(result['services_used'])}")

def demo_multi_agent_orchestration():
    print("\n🤝 MULTI-AGENT ORCHESTRATION")
    print("-" * 40)
    print("🔍 Starting comprehensive analysis with all agents...")
    
    result = orchestrator.orchestrate_full_analysis()
    
    if result['success']:
        print(f"✅ Analysis Complete!")
        print(f"🤖 Agents Involved: {result['agent_coordination_summary']['agents_involved']}")
        print(f"📊 Overall Health Score: {result['overall_scores']['overall']}/100")
        print(f"💡 Coordinated Recommendations: {len(result['coordinated_recommendations'])}")
        
        print("\n📈 Health Breakdown:")
        for metric, score in result['overall_scores'].items():
            if metric != 'overall':
                print(f"  • {metric.replace('_', ' ').title()}: {score}/100")
        
        print("\n🎯 Top Recommendations:")
        for i, rec in enumerate(result['coordinated_recommendations'][:3], 1):
            print(f"  {i}. [{rec['source']}] {rec['recommendation']}")
    else:
        print(f"❌ Analysis Failed: {result['error']}")

def main():
    print_banner()
    
    # Demo individual agents
    demo_cost_analysis()
    demo_operations_analysis() 
    demo_infrastructure_generation()
    
    # Demo multi-agent orchestration
    demo_multi_agent_orchestration()
    
    print("\n" + "=" * 60)
    print("🎉 AWS Operations Command Center Demo Complete!")
    print("📁 Frontend available at: frontend/index.html")
    print("🔧 API Server: python api_server.py")
    print("🚀 Ready for AWS deployment!")

if __name__ == "__main__":
    main()
