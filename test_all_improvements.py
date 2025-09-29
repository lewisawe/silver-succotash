#!/usr/bin/env python3
"""
Comprehensive test script for all implemented improvements
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports work correctly"""
    print("🔧 Testing Imports...")
    
    try:
        from config.settings import settings
        print("   ✅ Configuration imported")
        
        from utils.error_handling import safe_aws_call, handle_agent_error
        print("   ✅ Error handling imported")
        
        from utils.logging_config import cost_logger, ops_logger, infra_logger
        print("   ✅ Logging utilities imported")
        
        from utils.cache import cache, cached
        print("   ✅ Caching utilities imported")
        
        from schemas.agent_schemas import CostAnalysisRequest, validate_request
        print("   ✅ Validation schemas imported")
        
        from api.health import health_bp
        print("   ✅ Health check endpoints imported")
        
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration management"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        from config.settings import settings
        
        print(f"   AWS Region: {settings.aws_region}")
        print(f"   Max Retries: {settings.max_retries}")
        print(f"   Cache TTL: {settings.cache_ttl}")
        print(f"   Profiles: {list(settings.aws_profiles.keys())}")
        
        # Test validation
        settings.validate()
        print("   ✅ Configuration validation passed")
        return True
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_caching():
    """Test caching functionality"""
    print("\n💾 Testing Caching...")
    
    try:
        from utils.cache import cache, cached, get_cache_stats
        
        # Test basic cache operations
        cache.set("test_key", "test_value", 60)
        value = cache.get("test_key")
        assert value == "test_value"
        print("   ✅ Basic cache operations work")
        
        # Test decorator
        @cached(ttl=60)
        def test_function(x):
            return x * 2
        
        result1 = test_function(5)
        result2 = test_function(5)  # Should be cached
        assert result1 == result2 == 10
        print("   ✅ Cache decorator works")
        
        # Test stats
        stats = get_cache_stats()
        print(f"   Cache size: {stats['size']}")
        print("   ✅ Cache statistics work")
        
        return True
    except Exception as e:
        print(f"   ❌ Caching test failed: {e}")
        return False

def test_validation():
    """Test input validation"""
    print("\n✅ Testing Input Validation...")
    
    try:
        from schemas.agent_schemas import CostAnalysisRequest, validate_request
        
        # Test valid request
        valid_data = {"action": "full_analysis", "start_date": "2024-01-01"}
        result = validate_request(valid_data, CostAnalysisRequest)
        assert result['valid'] is True
        print("   ✅ Valid request validation works")
        
        # Test invalid request
        invalid_data = {"action": "invalid_action"}
        result = validate_request(invalid_data, CostAnalysisRequest)
        assert result['valid'] is False
        print("   ✅ Invalid request validation works")
        
        return True
    except Exception as e:
        print(f"   ❌ Validation test failed: {e}")
        return False

def test_agents():
    """Test agent initialization"""
    print("\n🤖 Testing Agent Initialization...")
    
    try:
        # Test cost intelligence agent
        from agent.cost_intelligence_agent import MultiAccountCostIntelligenceAgent
        cost_agent = MultiAccountCostIntelligenceAgent()
        print(f"   ✅ Cost agent initialized (Org: {cost_agent.is_org_account})")
        
        # Test operations intelligence agent
        from agent.operations_intelligence_agent import OrganizationsOperationsIntelligenceAgent
        ops_agent = OrganizationsOperationsIntelligenceAgent()
        print(f"   ✅ Operations agent initialized (Org: {ops_agent.is_org_account})")
        
        # Test infrastructure intelligence agent
        from agent.infrastructure_intelligence_agent import invoke
        test_payload = {"action": "assess_existing"}
        result = invoke(test_payload)
        print("   ✅ Infrastructure agent works")
        
        return True
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")
        return False

def test_health_checks():
    """Test health check functionality"""
    print("\n🏥 Testing Health Checks...")
    
    try:
        from api.health import check_aws_credentials, check_configuration
        
        # Test configuration check
        config_health = check_configuration()
        print(f"   Configuration health: {config_health['status']}")
        
        # Test AWS credentials check
        creds_health = check_aws_credentials()
        print(f"   AWS credentials health: {creds_health['status']}")
        
        print("   ✅ Health checks functional")
        return True
    except Exception as e:
        print(f"   ❌ Health check test failed: {e}")
        return False

def run_unit_tests():
    """Run pytest unit tests"""
    print("\n🧪 Running Unit Tests...")
    
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ All unit tests passed")
            return True
        else:
            print(f"   ❌ Some unit tests failed:")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"   ❌ Unit test execution failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AWS Operations Command Center - Comprehensive Test Suite")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Caching", test_caching),
        ("Validation", test_validation),
        ("Agents", test_agents),
        ("Health Checks", test_health_checks),
        ("Unit Tests", run_unit_tests)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All improvements implemented successfully!")
        print("\n🎯 Next Steps:")
        print("   1. Start the API server: python api_server.py")
        print("   2. Test endpoints: curl http://localhost:8000/health")
        print("   3. Run full analysis via API")
        print("   4. Check IMPROVEMENT_PLAN.md for Priority 3 items")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
