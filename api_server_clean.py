from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add current directory to path
sys.path.append('.')

# Import our agents and utilities
from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
from agent.infrastructure_intelligence_agent import invoke as infra_invoke
from agent.operations_intelligence_agent import OrganizationsOperationsIntelligenceAgent
from api.health import health_bp
from utils.logging_config import api_logger, log_with_context
from schemas.agent_schemas import validate_request, CostAnalysisRequest, InfrastructureRequest, OperationsRequest
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Register health check blueprint
app.register_blueprint(health_bp)

@app.route('/')
def home():
    return jsonify({
        'message': 'AWS Operations Command Center API',
        'version': '1.0.0',
        'agents': ['cost_intelligence', 'infrastructure_intelligence', 'operations_intelligence'],
        'endpoints': ['/cost/analyze', '/infrastructure/generate', '/operations/analyze', '/orchestrate/full-analysis', '/health', '/health/detailed']
    })

@app.route('/cost/analyze', methods=['POST'])
def cost_analyze():
    log_with_context(api_logger, logging.INFO, "Cost analysis requested")
    
    try:
        payload = request.get_json() or {}
        
        # Validate input
        validation = validate_request(payload, CostAnalysisRequest)
        if not validation['valid']:
            log_with_context(api_logger, logging.WARNING, "Invalid cost analysis request", errors=validation['errors'])
            return jsonify({'success': False, 'error': 'Invalid request', 'details': validation['errors']}), 400
        
        # Use cost intelligence agent
        agent = MultiAccountCostIntelligenceAgent()
        
        action = validation['data'].get('action', 'full_analysis')
        if action == 'full_analysis':
            result = agent.get_multi_account_costs()
            result['success'] = True
            result['agent'] = 'cost_intelligence'
        else:
            result = {'success': False, 'error': f'Unsupported action: {action}'}
        
        log_with_context(api_logger, logging.INFO, "Cost analysis completed", success=result.get('success', False))
        return jsonify(result)
    except Exception as e:
        log_with_context(api_logger, logging.ERROR, "Cost analysis failed", error=str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/infrastructure/generate', methods=['POST'])
def infrastructure_generate():
    log_with_context(api_logger, logging.INFO, "Infrastructure generation requested")
    
    try:
        payload = request.get_json() or {}
        
        # Validate input
        validation = validate_request(payload, InfrastructureRequest)
        if not validation['valid']:
            log_with_context(api_logger, logging.WARNING, "Invalid infrastructure request", errors=validation['errors'])
            return jsonify({'success': False, 'error': 'Invalid request', 'details': validation['errors']}), 400
        
        result = infra_invoke(validation['data'])
        log_with_context(api_logger, logging.INFO, "Infrastructure generation completed", success=result.get('success', False))
        return jsonify(result)
    except Exception as e:
        log_with_context(api_logger, logging.ERROR, "Infrastructure generation failed", error=str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/operations/analyze', methods=['POST'])
def operations_analyze():
    log_with_context(api_logger, logging.INFO, "Operations analysis requested")
    
    try:
        payload = request.get_json() or {}
        
        # Use operations intelligence agent
        agent = OrganizationsOperationsIntelligenceAgent()
        result = agent.get_organization_resource_inventory()
        result['success'] = True
        result['agent'] = 'operations_intelligence'
        
        log_with_context(api_logger, logging.INFO, "Operations analysis completed", success=result.get('success', False))
        return jsonify(result)
    except Exception as e:
        log_with_context(api_logger, logging.ERROR, "Operations analysis failed", error=str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/orchestrate/full-analysis', methods=['POST'])
def orchestrate_full_analysis():
    log_with_context(api_logger, logging.INFO, "Full analysis orchestration requested")
    
    try:
        payload = request.get_json() or {}
        
        # Use the orchestrator
        from orchestrator import LocalAgentOrchestrator
        orchestrator_instance = LocalAgentOrchestrator()
        
        result = orchestrator_instance.orchestrate_full_analysis(payload)
        log_with_context(api_logger, logging.INFO, "Full analysis completed", success=result.get('success', False))
        return jsonify(result)
    except Exception as e:
        log_with_context(api_logger, logging.ERROR, "Full analysis failed", error=str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting AWS Operations Command Center API Server...")
    print("=" * 60)
    print("📊 Available endpoints:")
    print("  - GET  /health")
    print("  - GET  /health/detailed")
    print("  - POST /cost/analyze")
    print("  - POST /infrastructure/generate") 
    print("  - POST /operations/analyze")
    print("  - POST /orchestrate/full-analysis")
    print("🌐 Dashboard: Open frontend/dashboard.html in your browser")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
