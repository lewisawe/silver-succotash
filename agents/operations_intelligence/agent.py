from bedrock_agentcore.runtime import BedrockAgentCoreApp
import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set
import networkx as nx

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

app = BedrockAgentCoreApp()

class OperationsIntelligenceAgent:
    def __init__(self):
        self.config = boto3.client('config', region_name='us-east-1')
        self.ec2 = boto3.client('ec2', region_name='us-east-1')
        self.rds = boto3.client('rds', region_name='us-east-1')
        self.elbv2 = boto3.client('elbv2', region_name='us-east-1')
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
    def map_resource_dependencies(self):
        """Create intelligent dependency map of AWS resources"""
        try:
            dependency_graph = nx.DiGraph()
            resources = {}
            
            # Get EC2 instances and their relationships
            ec2_instances = self.ec2.describe_instances()
            for reservation in ec2_instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    resources[instance_id] = {
                        'type': 'EC2',
                        'state': instance['State']['Name'],
                        'instance_type': instance['InstanceType'],
                        'vpc_id': instance.get('VpcId'),
                        'subnet_id': instance.get('SubnetId'),
                        'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])]
                    }
                    dependency_graph.add_node(instance_id, **resources[instance_id])
            
            # Get RDS instances
            rds_instances = self.rds.describe_db_instances()
            for db in rds_instances['DBInstances']:
                db_id = db['DBInstanceIdentifier']
                resources[db_id] = {
                    'type': 'RDS',
                    'engine': db['Engine'],
                    'instance_class': db['DBInstanceClass'],
                    'status': db['DBInstanceStatus'],
                    'multi_az': db.get('MultiAZ', False)
                }
                dependency_graph.add_node(db_id, **resources[db_id])
            
            # Get Load Balancers
            load_balancers = self.elbv2.describe_load_balancers()
            for lb in load_balancers['LoadBalancers']:
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                resources[lb_name] = {
                    'type': 'LoadBalancer',
                    'scheme': lb['Scheme'],
                    'state': lb['State']['Code'],
                    'vpc_id': lb.get('VpcId')
                }
                dependency_graph.add_node(lb_name, **resources[lb_name])
                
                # Map load balancer to target instances
                try:
                    target_groups = self.elbv2.describe_target_groups(
                        LoadBalancerArn=lb_arn
                    )
                    for tg in target_groups['TargetGroups']:
                        targets = self.elbv2.describe_target_health(
                            TargetGroupArn=tg['TargetGroupArn']
                        )
                        for target in targets['TargetHealthDescriptions']:
                            target_id = target['Target']['Id']
                            if target_id in resources:
                                dependency_graph.add_edge(lb_name, target_id, 
                                                        relationship='load_balances')
                except Exception:
                    pass
            
            # Analyze VPC relationships
            vpcs = self.ec2.describe_vpcs()
            for vpc in vpcs['Vpcs']:
                vpc_id = vpc['VpcId']
                
                # Find resources in this VPC
                vpc_resources = [rid for rid, rdata in resources.items() 
                               if rdata.get('vpc_id') == vpc_id]
                
                # Add VPC-level dependencies
                for i, res1 in enumerate(vpc_resources):
                    for res2 in vpc_resources[i+1:]:
                        if (resources[res1]['type'] == 'EC2' and 
                            resources[res2]['type'] == 'RDS'):
                            dependency_graph.add_edge(res1, res2, 
                                                    relationship='database_connection')
            
            # Calculate dependency metrics
            metrics = self._calculate_dependency_metrics(dependency_graph)
            
            # Identify critical resources
            critical_resources = self._identify_critical_resources(dependency_graph)
            
            # Generate dependency insights
            insights = self._generate_dependency_insights(dependency_graph, resources)
            
            return {
                'total_resources': len(resources),
                'resource_types': self._count_resource_types(resources),
                'dependency_graph': self._serialize_graph(dependency_graph),
                'metrics': metrics,
                'critical_resources': critical_resources,
                'insights': insights
            }
            
        except Exception as e:
            return {'error': f"Dependency mapping failed: {str(e)}"}
    
    def _calculate_dependency_metrics(self, graph: nx.DiGraph):
        """Calculate dependency graph metrics"""
        return {
            'total_nodes': graph.number_of_nodes(),
            'total_edges': graph.number_of_edges(),
            'density': nx.density(graph),
            'strongly_connected_components': len(list(nx.strongly_connected_components(graph))),
            'weakly_connected_components': len(list(nx.weakly_connected_components(graph)))
        }
    
    def _identify_critical_resources(self, graph: nx.DiGraph):
        """Identify resources that are critical to the infrastructure"""
        critical = []
        
        # Resources with high out-degree (many dependencies)
        out_degrees = dict(graph.out_degree())
        high_out_degree = [node for node, degree in out_degrees.items() if degree > 2]
        
        # Resources with high in-degree (many dependents)
        in_degrees = dict(graph.in_degree())
        high_in_degree = [node for node, degree in in_degrees.items() if degree > 2]
        
        # Calculate betweenness centrality
        try:
            centrality = nx.betweenness_centrality(graph)
            high_centrality = [node for node, cent in centrality.items() if cent > 0.1]
        except:
            high_centrality = []
        
        for node in set(high_out_degree + high_in_degree + high_centrality):
            critical.append({
                'resource_id': node,
                'criticality_reasons': [],
                'impact_if_removed': self._assess_removal_impact(graph, node)
            })
            
            if node in high_out_degree:
                critical[-1]['criticality_reasons'].append('High dependency count')
            if node in high_in_degree:
                critical[-1]['criticality_reasons'].append('Many resources depend on this')
            if node in high_centrality:
                critical[-1]['criticality_reasons'].append('Central to network topology')
        
        return critical
    
    def _assess_removal_impact(self, graph: nx.DiGraph, node: str):
        """Assess what would happen if a resource is removed"""
        # Find all nodes that would be affected
        affected_nodes = set()
        
        # Direct dependents
        dependents = list(graph.successors(node))
        affected_nodes.update(dependents)
        
        # Indirect dependents (nodes that depend on the dependents)
        for dependent in dependents:
            affected_nodes.update(nx.descendants(graph, dependent))
        
        return {
            'directly_affected': len(dependents),
            'total_affected': len(affected_nodes),
            'affected_resources': list(affected_nodes)[:10]  # Limit for readability
        }
    
    def _generate_dependency_insights(self, graph: nx.DiGraph, resources: Dict):
        """Generate actionable insights from dependency analysis"""
        insights = []
        
        # Check for single points of failure
        for node in graph.nodes():
            successors = list(graph.successors(node))
            if len(successors) > 3:
                insights.append({
                    'type': 'single_point_of_failure',
                    'resource': node,
                    'message': f"Resource {node} has {len(successors)} dependencies - consider redundancy",
                    'severity': 'high' if len(successors) > 5 else 'medium'
                })
        
        # Check for isolated resources
        isolated = [node for node in graph.nodes() 
                   if graph.degree(node) == 0]
        if isolated:
            insights.append({
                'type': 'isolated_resources',
                'resources': isolated,
                'message': f"Found {len(isolated)} isolated resources that may be unused",
                'severity': 'low'
            })
        
        # Check for circular dependencies
        try:
            cycles = list(nx.simple_cycles(graph))
            if cycles:
                insights.append({
                    'type': 'circular_dependencies',
                    'cycles': cycles[:5],  # Limit for readability
                    'message': f"Found {len(cycles)} circular dependencies",
                    'severity': 'medium'
                })
        except:
            pass
        
        return insights
    
    def _count_resource_types(self, resources: Dict):
        """Count resources by type"""
        type_counts = {}
        for resource_data in resources.values():
            resource_type = resource_data['type']
            type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
        return type_counts
    
    def _serialize_graph(self, graph: nx.DiGraph):
        """Convert graph to serializable format"""
        return {
            'nodes': [{'id': node, **data} for node, data in graph.nodes(data=True)],
            'edges': [{'source': u, 'target': v, **data} 
                     for u, v, data in graph.edges(data=True)]
        }
    
    def analyze_performance_bottlenecks(self):
        """Identify performance bottlenecks in the infrastructure"""
        try:
            bottlenecks = []
            
            # Check EC2 instances for high CPU/memory usage
            ec2_instances = self.ec2.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )
            
            for reservation in ec2_instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    
                    try:
                        # Get CPU utilization
                        cpu_metrics = self.cloudwatch.get_metric_statistics(
                            Namespace='AWS/EC2',
                            MetricName='CPUUtilization',
                            Dimensions=[
                                {'Name': 'InstanceId', 'Value': instance_id}
                            ],
                            StartTime=datetime.now() - timedelta(hours=24),
                            EndTime=datetime.now(),
                            Period=3600,
                            Statistics=['Average', 'Maximum']
                        )
                        
                        if cpu_metrics['Datapoints']:
                            avg_cpu = sum(d['Average'] for d in cpu_metrics['Datapoints']) / len(cpu_metrics['Datapoints'])
                            max_cpu = max(d['Maximum'] for d in cpu_metrics['Datapoints'])
                            
                            if avg_cpu > 80 or max_cpu > 95:
                                bottlenecks.append({
                                    'resource_id': instance_id,
                                    'type': 'high_cpu_utilization',
                                    'avg_cpu': round(avg_cpu, 2),
                                    'max_cpu': round(max_cpu, 2),
                                    'recommendation': 'Consider upgrading instance type or optimizing application',
                                    'severity': 'high' if max_cpu > 95 else 'medium'
                                })
                    except Exception:
                        pass
            
            # Check RDS instances for performance issues
            rds_instances = self.rds.describe_db_instances()
            for db in rds_instances['DBInstances']:
                if db['DBInstanceStatus'] == 'available':
                    db_id = db['DBInstanceIdentifier']
                    
                    try:
                        # Check database connections
                        conn_metrics = self.cloudwatch.get_metric_statistics(
                            Namespace='AWS/RDS',
                            MetricName='DatabaseConnections',
                            Dimensions=[
                                {'Name': 'DBInstanceIdentifier', 'Value': db_id}
                            ],
                            StartTime=datetime.now() - timedelta(hours=24),
                            EndTime=datetime.now(),
                            Period=3600,
                            Statistics=['Average', 'Maximum']
                        )
                        
                        if conn_metrics['Datapoints']:
                            max_connections = max(d['Maximum'] for d in conn_metrics['Datapoints'])
                            
                            # Rough estimate of connection limit based on instance class
                            instance_class = db['DBInstanceClass']
                            estimated_limit = 100 if 'micro' in instance_class else 500
                            
                            if max_connections > estimated_limit * 0.8:
                                bottlenecks.append({
                                    'resource_id': db_id,
                                    'type': 'high_database_connections',
                                    'max_connections': max_connections,
                                    'estimated_limit': estimated_limit,
                                    'recommendation': 'Consider connection pooling or upgrading instance',
                                    'severity': 'medium'
                                })
                    except Exception:
                        pass
            
            return {
                'bottlenecks': bottlenecks,
                'total_issues': len(bottlenecks),
                'high_severity': len([b for b in bottlenecks if b.get('severity') == 'high']),
                'recommendations': self._generate_performance_recommendations(bottlenecks)
            }
            
        except Exception as e:
            return {'error': f"Performance analysis failed: {str(e)}"}
    
    def _generate_performance_recommendations(self, bottlenecks: List[Dict]):
        """Generate performance optimization recommendations"""
        recommendations = []
        
        cpu_issues = [b for b in bottlenecks if b['type'] == 'high_cpu_utilization']
        if cpu_issues:
            recommendations.append({
                'category': 'compute_optimization',
                'priority': 'high',
                'recommendation': f"Optimize {len(cpu_issues)} instances with high CPU usage",
                'actions': [
                    'Analyze application performance',
                    'Consider vertical scaling (larger instance types)',
                    'Implement horizontal scaling (Auto Scaling)',
                    'Optimize application code and queries'
                ]
            })
        
        db_issues = [b for b in bottlenecks if b['type'] == 'high_database_connections']
        if db_issues:
            recommendations.append({
                'category': 'database_optimization',
                'priority': 'medium',
                'recommendation': f"Optimize {len(db_issues)} databases with connection issues",
                'actions': [
                    'Implement connection pooling',
                    'Optimize database queries',
                    'Consider read replicas for read-heavy workloads',
                    'Upgrade database instance if needed'
                ]
            })
        
        return recommendations

operations_agent = OperationsIntelligenceAgent()

@app.entrypoint
def invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Operations Intelligence Agent - Smart dependency mapping and performance analysis"""
    try:
        action = payload.get("action", "map_dependencies")
        
        if action == "map_dependencies":
            result = operations_agent.map_resource_dependencies()
            
        elif action == "analyze_performance":
            result = operations_agent.analyze_performance_bottlenecks()
            
        elif action == "full_operations_analysis":
            # Comprehensive operations analysis
            dependencies = operations_agent.map_resource_dependencies()
            performance = operations_agent.analyze_performance_bottlenecks()
            
            result = {
                'dependencies': dependencies,
                'performance': performance,
                'summary': {
                    'total_resources': dependencies.get('total_resources', 0),
                    'critical_resources': len(dependencies.get('critical_resources', [])),
                    'performance_issues': performance.get('total_issues', 0)
                }
            }
            
        else:
            result = {
                'message': 'Operations Intelligence Agent ready. Available actions: map_dependencies, analyze_performance, full_operations_analysis'
            }
        
        result['agent'] = 'operations_intelligence'
        result['timestamp'] = datetime.now().isoformat()
        result['success'] = True
        
        return result
        
    except Exception as e:
        return {
            'agent': 'operations_intelligence',
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    app.run()
