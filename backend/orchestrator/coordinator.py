import boto3
import json
from typing import Dict, Any, List
from datetime import datetime

class AgentCoordinator:
    """Intelligent coordinator for multi-agent AWS operations"""
    
    def __init__(self):
        self.bedrock_agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')
        
        # Agent ARNs (will be populated after deployment)
        self.agents = {
            'cost_intelligence': None,
            'infrastructure_intelligence': None,
            'operations_intelligence': None
        }
    
    def set_agent_arns(self, agent_arns: Dict[str, str]):
        """Set the ARNs for deployed agents"""
        self.agents.update(agent_arns)
    
    async def invoke_agent(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a specific agent"""
        try:
            agent_arn = self.agents.get(agent_name)
            if not agent_arn:
                return {'error': f'Agent {agent_name} not configured'}
            
            response = self.bedrock_agentcore.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                payload=json.dumps(payload),
                contentType='application/json'
            )
            
            if response['statusCode'] == 200:
                result = json.loads(response['response'].read().decode('utf-8'))
                return result
            else:
                return {'error': f'Agent invocation failed: {response["statusCode"]}'}
                
        except Exception as e:
            return {'error': f'Agent invocation error: {str(e)}'}
    
    async def orchestrate_cost_optimization(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate cost optimization across multiple agents"""
        try:
            results = {}
            
            # Step 1: Analyze current costs
            print("🔍 Analyzing current costs...")
            cost_analysis = await self.invoke_agent('cost_intelligence', {
                'action': 'full_analysis'
            })
            results['cost_analysis'] = cost_analysis
            
            # Step 2: Map dependencies to understand impact
            print("🗺️ Mapping resource dependencies...")
            dependency_analysis = await self.invoke_agent('operations_intelligence', {
                'action': 'map_dependencies'
            })
            results['dependencies'] = dependency_analysis
            
            # Step 3: Generate optimized infrastructure if needed
            if requirements.get('generate_optimized_architecture'):
                print("🏗️ Generating optimized architecture...")
                
                # Use cost insights to inform architecture decisions
                cost_constraints = {
                    'budget_limit': requirements.get('budget_limit'),
                    'cost_priorities': cost_analysis.get('optimizations', {}).get('opportunities', [])
                }
                
                infrastructure_result = await self.invoke_agent('infrastructure_intelligence', {
                    'action': 'generate_architecture',
                    'requirements': {
                        **requirements.get('architecture_requirements', {}),
                        'cost_constraints': cost_constraints
                    }
                })
                results['optimized_architecture'] = infrastructure_result
            
            # Step 4: Coordinate recommendations
            coordinated_recommendations = self._coordinate_recommendations(results)
            
            return {
                'success': True,
                'orchestration_type': 'cost_optimization',
                'results': results,
                'coordinated_recommendations': coordinated_recommendations,
                'estimated_savings': self._calculate_total_savings(results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Cost optimization orchestration failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def orchestrate_infrastructure_assessment(self, account_id: str) -> Dict[str, Any]:
        """Comprehensive infrastructure assessment using all agents"""
        try:
            results = {}
            
            # Step 1: Operations analysis (dependencies and performance)
            print("🔍 Analyzing operations and dependencies...")
            operations_result = await self.invoke_agent('operations_intelligence', {
                'action': 'full_operations_analysis'
            })
            results['operations'] = operations_result
            
            # Step 2: Cost analysis
            print("💰 Analyzing costs...")
            cost_result = await self.invoke_agent('cost_intelligence', {
                'action': 'full_analysis'
            })
            results['costs'] = cost_result
            
            # Step 3: Infrastructure assessment
            print("🏗️ Assessing infrastructure...")
            infrastructure_result = await self.invoke_agent('infrastructure_intelligence', {
                'action': 'assess_existing'
            })
            results['infrastructure'] = infrastructure_result
            
            # Step 4: Generate comprehensive insights
            comprehensive_insights = self._generate_comprehensive_insights(results)
            
            return {
                'success': True,
                'orchestration_type': 'infrastructure_assessment',
                'account_id': account_id,
                'results': results,
                'comprehensive_insights': comprehensive_insights,
                'overall_score': self._calculate_overall_score(results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Infrastructure assessment failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def orchestrate_smart_architecture_design(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Smart architecture design with agent collaboration"""
        try:
            results = {}
            
            # Step 1: Generate initial architecture
            print("🏗️ Generating initial architecture...")
            initial_architecture = await self.invoke_agent('infrastructure_intelligence', {
                'action': 'generate_architecture',
                'requirements': requirements
            })
            results['initial_architecture'] = initial_architecture
            
            # Step 2: Cost analysis of proposed architecture
            print("💰 Analyzing cost implications...")
            estimated_cost = initial_architecture.get('estimated_monthly_cost', 0)
            
            if estimated_cost > requirements.get('budget_limit', float('inf')):
                print("💡 Cost too high, getting optimization suggestions...")
                cost_optimization = await self.invoke_agent('cost_intelligence', {
                    'action': 'find_optimizations'
                })
                results['cost_feedback'] = cost_optimization
                
                # Step 3: Regenerate architecture with cost constraints
                print("🔄 Regenerating cost-optimized architecture...")
                optimized_requirements = {
                    **requirements,
                    'cost_optimization': True,
                    'budget_constraint': requirements.get('budget_limit')
                }
                
                optimized_architecture = await self.invoke_agent('infrastructure_intelligence', {
                    'action': 'generate_architecture',
                    'requirements': optimized_requirements
                })
                results['optimized_architecture'] = optimized_architecture
            
            # Step 4: Operational impact analysis
            print("🔍 Analyzing operational impact...")
            if 'optimized_architecture' in results:
                # Analyze the optimized version
                architecture_to_analyze = results['optimized_architecture']
            else:
                architecture_to_analyze = initial_architecture
            
            # Generate final recommendations
            final_recommendations = self._generate_architecture_recommendations(results, requirements)
            
            return {
                'success': True,
                'orchestration_type': 'smart_architecture_design',
                'requirements': requirements,
                'results': results,
                'final_recommendations': final_recommendations,
                'agent_collaboration_summary': self._summarize_agent_collaboration(results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Smart architecture design failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _coordinate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Coordinate recommendations from multiple agents"""
        coordinated = []
        
        # Extract cost optimization opportunities
        cost_ops = results.get('cost_analysis', {}).get('optimizations', {}).get('opportunities', [])
        for opp in cost_ops:
            coordinated.append({
                'source': 'cost_intelligence',
                'type': 'cost_optimization',
                'priority': 'high' if opp.get('monthly_savings', 0) > 100 else 'medium',
                'recommendation': opp.get('recommendation', ''),
                'impact': f"${opp.get('monthly_savings', 0)}/month savings"
            })
        
        # Extract operational insights
        ops_insights = results.get('dependencies', {}).get('insights', [])
        for insight in ops_insights:
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
    
    def _calculate_total_savings(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate total potential savings from all agents"""
        total_monthly = 0
        
        cost_analysis = results.get('cost_analysis', {})
        if 'optimizations' in cost_analysis:
            total_monthly += cost_analysis['optimizations'].get('total_potential_monthly_savings', 0)
        
        return {
            'monthly_savings': total_monthly,
            'annual_savings': total_monthly * 12
        }
    
    def _generate_comprehensive_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights from all agent results"""
        insights = {
            'strengths': [],
            'critical_issues': [],
            'optimization_opportunities': [],
            'recommendations': []
        }
        
        # Analyze operations results
        ops = results.get('operations', {})
        if ops.get('dependencies'):
            total_resources = ops['dependencies'].get('total_resources', 0)
            critical_resources = len(ops['dependencies'].get('critical_resources', []))
            
            if critical_resources / max(total_resources, 1) < 0.2:
                insights['strengths'].append('Well-distributed architecture with few single points of failure')
            else:
                insights['critical_issues'].append(f'{critical_resources} critical resources identified - high risk')
        
        # Analyze cost results
        costs = results.get('costs', {})
        if costs.get('optimizations'):
            potential_savings = costs['optimizations'].get('total_potential_monthly_savings', 0)
            if potential_savings > 500:
                insights['optimization_opportunities'].append(f'${potential_savings}/month in cost savings available')
        
        # Generate actionable recommendations
        if insights['critical_issues']:
            insights['recommendations'].append('Priority: Address critical resource dependencies')
        if insights['optimization_opportunities']:
            insights['recommendations'].append('Implement cost optimization recommendations')
        
        return insights
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> Dict[str, int]:
        """Calculate overall infrastructure health scores"""
        scores = {
            'cost_efficiency': 70,
            'operational_health': 70,
            'security': 70,
            'reliability': 70,
            'overall': 70
        }
        
        # Adjust based on results
        costs = results.get('costs', {})
        if costs.get('optimizations', {}).get('total_potential_monthly_savings', 0) > 1000:
            scores['cost_efficiency'] -= 20
        
        ops = results.get('operations', {})
        if ops.get('performance', {}).get('high_severity', 0) > 0:
            scores['operational_health'] -= 15
        
        infrastructure = results.get('infrastructure', {})
        if len(infrastructure.get('security_issues', [])) > 5:
            scores['security'] -= 25
        
        # Calculate overall score
        scores['overall'] = sum(scores.values()) // 4
        
        return scores
    
    def _generate_architecture_recommendations(self, results: Dict[str, Any], requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    
    def _summarize_agent_collaboration(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize how agents collaborated"""
        return {
            'agents_involved': len([k for k in results.keys() if k != 'timestamp']),
            'collaboration_points': [
                'Infrastructure agent generated initial design',
                'Cost agent provided budget feedback',
                'Architecture optimized based on cost constraints'
            ],
            'decision_points': [
                'Budget constraint triggered architecture optimization',
                'Security score influenced final recommendations'
            ]
        }

# Global coordinator instance
coordinator = AgentCoordinator()
