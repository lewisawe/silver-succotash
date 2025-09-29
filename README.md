# AWS Operations Command Center

A multi-agent AI system built with Amazon Bedrock AgentCore that provides intelligent AWS operations management across entire organizations.

## What It Does

The system uses three specialized AI agents that work together to analyze AWS infrastructure:

- **Cost Intelligence Agent**: Discovers hidden usage patterns across multiple AWS accounts, separating actual consumption from credits
- **Operations Intelligence Agent**: Scans resources across your AWS organization using cross-account roles
- **Infrastructure Intelligence Agent**: Generates architecture recommendations and security assessments

## Key Features

- **Self-discovering agents** that automatically detect AWS Organizations and adapt to any environment
- **Cross-account analysis** with secure IAM role assumption
- **Real cost visibility** showing actual usage vs credits ($255.22 discovered in our testing)
- **Multi-account resource inventory** (90+ resources across organization accounts)
- **Production-ready error handling** with graceful fallbacks
- **Agent coordination** through memory service and orchestrator

## Quick Start

### Prerequisites

- Python 3.8+
- AWS CLI configured with appropriate permissions
- Amazon Bedrock AgentCore CLI installed

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd aws_operations_command_center

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Setup Cross-Account Access (Optional)

For full organization analysis, deploy cross-account roles:

```bash
# Setup IAM roles across organization accounts
python setup_cross_account_roles.py

# Deploy CloudFormation templates to member accounts
python deploy_with_profiles.py
```

### Running the System

```bash
# Test individual agents
python quick_test.py

# Start the web dashboard
python start_demo.py

# Run comprehensive tests
python test_real_agents.py
```

## Architecture

### Agent Structure

Each agent follows the AgentCore pattern:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    # Agent logic here
    return result
```

### Self-Discovery

Agents automatically detect their AWS environment:

- Check if running in AWS Organizations management account
- Discover available accounts and permissions
- Adapt behavior based on capabilities

### Cross-Account Access

Uses secure IAM roles with external ID validation:

- `OrganizationAccountAccessRole` in each member account
- Read-only permissions with least privilege
- Automatic role assumption for resource scanning

## API Endpoints

- `POST /cost/analyze` - Multi-account cost analysis
- `POST /operations/analyze` - Resource inventory scan  
- `POST /infrastructure/generate` - Architecture recommendations
- `POST /orchestrate/full-analysis` - Coordinated multi-agent analysis

## Configuration

The system uses environment-based configuration:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_PROFILE_MANAGEMENT=default
export AWS_PROFILE_CRUMMYFUN=simi-ops
export AWS_PROFILE_ACHAMIN=achamin

# Agent Configuration  
export MAX_RETRIES=3
export PARALLEL_WORKERS=5
export DEBUG=false
```

## Testing

```bash
# Quick functionality test
python quick_test.py

# Comprehensive real-world tests
python test_real_agents.py

# Cross-account access verification
python test_cross_account.py
```

## Deployment

### Local Development

```bash
python api_server.py
```

### AgentCore Deployment

```bash
# Deploy individual agents
agentcore deploy --agent cost_intelligence_agent
agentcore deploy --agent operations_intelligence_agent  
agentcore deploy --agent infrastructure_intelligence_agent
```

## Results

In our testing environment:

- **Cost Discovery**: $255.22 in actual usage across 3 accounts (hidden by $255.21 in credits)
- **Resource Inventory**: 90 resources discovered across organization
- **Account Coverage**: 100% for costs, 67% for resources (normal for empty accounts)
- **Agent Coordination**: All 3 agents working together with shared context

## Troubleshooting

### Common Issues

**AgentCore deployment failures**: Use local mode fallback in orchestrator
**Cross-account access denied**: Verify IAM roles are deployed correctly  
**Memory service errors**: Check context size limits (1MB max)
**Gateway timeouts**: System automatically falls back to local agents

### Debug Mode

```bash
export DEBUG=true
python test_real_agents.py
```

## Architecture Decisions

### Why Multi-Agent?

Each agent specializes in a specific domain (cost, operations, infrastructure) but they share context through the memory service. This provides better insights than any single agent could generate.

### Why Self-Discovery?

Eliminates manual configuration and makes the system work in any AWS environment without changes. Agents adapt to their permissions and capabilities automatically.

### Why Cross-Account?

True organizational visibility requires access to all accounts. The secure IAM role approach provides this while maintaining AWS security boundaries.

## Contributing

The system is designed for extensibility:

- Add new agents by implementing the AgentCore pattern
- Extend resource scanning by adding new AWS service clients
- Improve recommendations by enhancing the analysis algorithms

## License

[Add your license here]
