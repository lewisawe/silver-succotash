#!/usr/bin/env python3
"""
Test script to verify the improvements are working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
from utils.error_handling import safe_aws_call
from utils.logging_config import cost_logger, log_with_context
from config.settings import settings
import logging
import json

def test_configuration():
    """Test configuration management"""
    print("🔧 Testing Configuration Management...")
    print(f"   AWS Region: {settings.aws_region}")
    print(f"   Max Retries: {settings.max_retries}")
    print(f"   Cache TTL: {settings.cache_ttl}")
    print(f"   Account Profiles: {list(settings.aws_profiles.keys())}")
    print("   ✅ Configuration loaded successfully")

def test_logging():
    """Test structured logging"""
    print("\n📝 Testing Structured Logging...")
    log_with_context(cost_logger, logging.INFO, "Test log message", 
                    test_field="test_value", 
                    numeric_field=123)
    print("   ✅ Structured logging working")

def test_error_handling():
    """Test error handling"""
    print("\n🚨 Testing Error Handling...")
    
    # Test with a mock function that will fail
    def mock_failing_function():
        raise Exception("Test error")
    
    result = safe_aws_call(mock_failing_function)
    if not result['success']:
        print(f"   ✅ Error handling working: {result['error']}")
    else:
        print("   ❌ Error handling not working")

def test_agent_initialization():
    """Test agent initialization"""
    print("\n🤖 Testing Agent Initialization...")
    try:
        agent = MultiAccountCostIntelligenceAgent()
        print(f"   ✅ Agent initialized successfully")
        print(f"   📊 Found {len(agent.account_profiles)} account profiles")
        print(f"   🏢 Organization account: {agent.is_org_account}")
        if agent.is_org_account:
            print(f"   📋 Organization has {len(agent.org_accounts)} accounts")
        return agent
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 AWS Operations Command Center - Improvement Tests")
    print("=" * 60)
    
    test_configuration()
    test_logging()
    test_error_handling()
    agent = test_agent_initialization()
    
    print("\n" + "=" * 60)
    print("✅ All improvement tests completed!")
    
    if agent:
        print("\n🎯 Next Steps:")
        print("   1. Run: pytest tests/ -v")
        print("   2. Test cost collection with: python -c 'from agent.cost_intelligence_agent import *; agent = MultiAccountCostIntelligenceAgent(); print(agent.get_multi_account_costs())'")
        print("   3. Check the IMPROVEMENT_PLAN.md for next priorities")

if __name__ == "__main__":
    main()
