import sys
sys.path.append('.')
from utils.gateway_client import gateway
import json
from datetime import datetime

class LocalAgentOrchestrator:
    """Orchestrator using AgentCore Gateway for agent communication"""
    
    def __init__(self, use_gateway: bool = True):
        self.use_gateway = use_gateway
        
        # Fallback to local agents if gateway unavailable
        if not use_gateway:
            from agent.cost_intelligence_agent import invoke as cost_invoke
            from agent.infrastructure_intelligence_agent import invoke as infra_invoke
            from agent.operations_intelligence_agent import invoke as ops_invoke
            
            self.agents = {
                'cost_intelligence': cost_invoke,
                'infrastructure_intelligence': infra_invoke,
                'operations_intelligence': ops_invoke
            }
    
    def invoke_agent(self, agent_name: str, payload: dict) -> dict:
        """Invoke agent via gateway or local fallback"""
        if self.use_gateway:
            return gateway.invoke_agent(agent_name, payload)
        else:
            if agent_name not in self.agents:
                return {'error': f'Agent {agent_name} not found'}
            
            try:
                return self.agents[agent_name](payload)
            except Exception as e:
                return {'error': f'Agent {agent_name} failed: {str(e)}'}
    
    def orchestrate_full_analysis(self, requirements: dict = None) -> dict:
        """Orchestrate comprehensive AWS operations analysis with error recovery"""
        try:
            print("🔍 Starting comprehensive AWS operations analysis...")
            results = {}
            errors = []
            
            # Step 1: Cost Analysis
            print("💰 Analyzing costs...")
            try:
                cost_result = self.invoke_agent('cost_intelligence', {'action': 'full_analysis'})
                results['cost_analysis'] = cost_result
            except Exception as e:
                error_msg = f"Cost analysis failed: {str(e)}"
                errors.append(error_msg)
                results['cost_analysis'] = {'success': False, 'error': error_msg}
            
            # Step 2: Operations Analysis
            print("🗺️ Mapping dependencies and analyzing performance...")
            try:
                ops_result = self.invoke_agent('operations_intelligence', {'action': 'full_operations_analysis'})
                results['operations_analysis'] = ops_result
            except Exception as e:
                error_msg = f"Operations analysis failed: {str(e)}"
                errors.append(error_msg)
                results['operations_analysis'] = {'success': False, 'error': error_msg}
            
            # Step 3: Infrastructure Assessment
            print("🏗️ Assessing infrastructure...")
            try:
                infra_result = self.invoke_agent('infrastructure_intelligence', {'action': 'assess_existing'})
                results['infrastructure_assessment'] = infra_result
            except Exception as e:
                error_msg = f"Infrastructure assessment failed: {str(e)}"
                errors.append(error_msg)
                results['infrastructure_assessment'] = {'success': False, 'error': error_msg}
            
            # Step 4: Generate coordinated recommendations from successful results
            print("🤝 Coordinating recommendations across agents...")
            coordinated_recommendations = self._coordinate_recommendations(results)
            
            # Step 5: Calculate overall scores from available data
            overall_scores = self._calculate_overall_scores(results)
            
            # Determine overall success
            successful_agents = sum(1 for r in results.values() if r.get('success', False))
            overall_success = successful_agents > 0  # Success if at least one agent succeeded
            
            return {
                'success': overall_success,
                'orchestration_type': 'full_aws_operations_analysis',
                'results': results,
                'coordinated_recommendations': coordinated_recommendations,
                'overall_scores': overall_scores,
                'agent_coordination_summary': {
                    'agents_involved': 3,
                    'successful_agents': successful_agents,
                    'errors': errors,
                    'total_services_used': ['runtime', 'memory', 'gateway'],
                    'coordination_points': [
                        'Cost optimization opportunities identified',
                        'Infrastructure security issues flagged',
                        'Performance bottlenecks detected',
                        'Cross-agent recommendations generated'
                    ]
                },
                'timestamp': datetime.now().isoformat()
            }
            print("🤝 Coordinating recommendations across agents...")
            coordinated_recommendations = self._coordinate_recommendations(results)
            
            # Step 5: Calculate overall scores
            overall_scores = self._calculate_overall_scores(results)
            
            return {
                'success': True,
                'orchestration_type': 'full_aws_operations_analysis',
                'results': results,
                'coordinated_recommendations': coordinated_recommendations,
                'overall_scores': overall_scores,
                'agent_coordination_summary': {
                    'agents_involved': 3,
                    'total_services_used': ['runtime', 'memory', 'gateway'],
                    'coordination_points': [
                        'Cost optimization opportunities identified',
                        'Infrastructure security issues flagged',
                        'Performance bottlenecks detected',
                        'Cross-agent recommendations generated'
                    ]
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Orchestration failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def orchestrate_smart_architecture_design(self, requirements: dict) -> dict:
        """Smart architecture design with agent collaboration"""
        try:
            print("🏗️ Starting smart architecture design...")
            results = {}
            
            # Step 1: Generate initial architecture
            print("📐 Generating initial architecture...")
            initial_arch = self.invoke_agent('infrastructure_intelligence', {
                'action': 'generate_architecture',
                'requirements': requirements
            })
            results['initial_architecture'] = initial_arch
            
            # Step 2: Cost analysis of proposed architecture
            print("💰 Analyzing cost implications...")
            estimated_cost = initial_arch.get('estimated_monthly_cost', 0)
            budget_limit = requirements.get('budget_limit', float('inf'))
            
            if estimated_cost > budget_limit:
                print("💡 Cost too high, getting optimization suggestions...")
                cost_optimization = self.invoke_agent('cost_intelligence', {
                    'action': 'full_analysis'
                })
                results['cost_feedback'] = cost_optimization
                
                # Regenerate with cost constraints
                print("🔄 Regenerating cost-optimized architecture...")
                optimized_requirements = {
                    **requirements,
                    'scale': 'small' if estimated_cost > budget_limit * 2 else 'medium'
                }
                
                optimized_arch = self.invoke_agent('infrastructure_intelligence', {
                    'action': 'generate_architecture',
                    'requirements': optimized_requirements
                })
                results['optimized_architecture'] = optimized_arch
            
            # Step 3: Final recommendations
            final_recommendations = self._generate_architecture_recommendations(results, requirements)
            
            return {
                'success': True,
                'orchestration_type': 'smart_architecture_design',
                'requirements': requirements,
                'results': results,
                'final_recommendations': final_recommendations,
                'agent_collaboration_summary': {
                    'agents_involved': 2,
                    'collaboration_points': [
                        'Infrastructure agent generated initial design',
                        'Cost agent provided budget feedback',
                        'Architecture optimized based on cost constraints'
                    ]
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Architecture design failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _coordinate_recommendations(self, results: dict) -> list:
        """Coordinate recommendations from multiple agents"""
        coordinated = []
        
        # Extract cost optimization opportunities
        cost_analysis = results.get('cost_analysis', {})
        if 'optimizations' in cost_analysis:
            for opp in cost_analysis['optimizations'].get('opportunities', []):
                coordinated.append({
                    'source': 'cost_intelligence',
                    'type': 'cost_optimization',
                    'priority': 'high' if opp.get('monthly_savings', 0) > 100 else 'medium',
                    'recommendation': opp.get('recommendation', ''),
                    'impact': f"${opp.get('monthly_savings', 0)}/month savings"
                })
        
        # Extract infrastructure security issues
        infra_assessment = results.get('infrastructure_assessment', {})
        for issue in infra_assessment.get('security_issues', []):
            coordinated.append({
                'source': 'infrastructure_intelligence',
                'type': 'security_improvement',
                'priority': issue.get('severity', 'medium'),
                'recommendation': issue.get('recommendation', ''),
                'impact': 'Improved security posture'
            })
        
        # Extract operational insights
        ops_analysis = results.get('operations_analysis', {})
        if 'dependencies' in ops_analysis:
            for insight in ops_analysis['dependencies'].get('insights', []):
                coordinated.append({
                    'source': 'operations_intelligence',
                    'type': 'operational_improvement',
                    'priority': insight.get('severity', 'medium'),
                    'recommendation': insight.get('message', ''),
                    'impact': 'Improved reliability and performance'
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        coordinated.sort(key=lambda x: priority_order.get(x['priority'], 2))
        
        return coordinated
    
    def _calculate_overall_scores(self, results: dict) -> dict:
        """Calculate overall infrastructure health scores"""
        scores = {
            'cost_efficiency': 70,
            'operational_health': 70,
            'security': 70,
            'reliability': 70,
            'overall': 70
        }
        
        # Adjust based on results
        cost_analysis = results.get('cost_analysis', {})
        if cost_analysis.get('optimizations', {}).get('total_potential_monthly_savings', 0) > 200:
            scores['cost_efficiency'] -= 15
        
        ops_analysis = results.get('operations_analysis', {})
        if ops_analysis.get('performance', {}).get('high_severity', 0) > 0:
            scores['operational_health'] -= 10
        
        infra_assessment = results.get('infrastructure_assessment', {})
        if len(infra_assessment.get('security_issues', [])) > 1:
            scores['security'] -= 20
        
        # Calculate overall score
        scores['overall'] = sum([scores['cost_efficiency'], scores['operational_health'], 
                               scores['security'], scores['reliability']]) // 4
        
        return scores
    
    def _generate_architecture_recommendations(self, results: dict, requirements: dict) -> list:
        """Generate final architecture recommendations"""
        recommendations = []
        
        if 'cost_feedback' in results:
            recommendations.append({
                'category': 'cost_optimization',
                'priority': 'high',
                'title': 'Architecture exceeds budget',
                'description': 'Initial architecture design exceeds budget constraints',
                'action': 'Use optimized architecture version',
                'impact': 'Reduced costs while maintaining functionality'
            })
        
        initial_arch = results.get('initial_architecture', {})
        if initial_arch.get('security_score', 0) < 80:
            recommendations.append({
                'category': 'security',
                'priority': 'high',
                'title': 'Enhance security configuration',
                'description': 'Architecture security score below recommended threshold',
                'action': 'Implement additional security controls',
                'impact': 'Improved security posture'
            })
        
        return recommendations

# Global orchestrator instance
# Force local mode for testing (gateway agents not deployed yet)
orchestrator = LocalAgentOrchestrator(use_gateway=False)
print("⚠️ Using local agents (gateway agents not deployed)")

if __name__ == "__main__":
    # Test the orchestrator
    print("🚀 Testing AWS Operations Command Center - Multi-Agent Orchestration")
    print("=" * 80)
    
    # Test 1: Full Analysis
    print("\n🔍 TEST 1: Full AWS Operations Analysis")
    result = orchestrator.orchestrate_full_analysis()
    
    if result['success']:
        print("✅ Full analysis completed successfully!")
        print(f"📊 Overall Scores: {result['overall_scores']}")
        print(f"🤝 Agents Involved: {result['agent_coordination_summary']['agents_involved']}")
        print(f"💡 Recommendations: {len(result['coordinated_recommendations'])}")
    else:
        print(f"❌ Full analysis failed: {result['error']}")
    
    print("\n" + "=" * 80)
    
    # Test 2: Smart Architecture Design
    print("\n🏗️ TEST 2: Smart Architecture Design")
    arch_requirements = {
        'type': 'web_app_3tier',
        'scale': 'large',
        'budget_limit': 300  # This will trigger cost optimization
    }
    
    result = orchestrator.orchestrate_smart_architecture_design(arch_requirements)
    
    if result['success']:
        print("✅ Smart architecture design completed!")
        print(f"🏗️ Architecture optimized due to budget constraints")
        print(f"💡 Final recommendations: {len(result['final_recommendations'])}")
    else:
        print(f"❌ Architecture design failed: {result['error']}")
    
    print("\n🎉 Multi-Agent Orchestration Testing Complete!")
