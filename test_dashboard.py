#!/usr/bin/env python3
"""
Test script to demonstrate the dashboard with real data
"""

import sys
import os
import json
import webbrowser
import threading
import time
from flask import Flask

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_api_server():
    """Start the API server in a separate thread"""
    from api_server import app
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

def test_dashboard():
    """Test the dashboard functionality"""
    print("🎨 AWS Operations Command Center - Dashboard Test")
    print("=" * 60)
    
    # Start API server in background
    print("🚀 Starting API server...")
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Test API endpoints
    import requests
    
    try:
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        health_response = requests.get('http://localhost:8000/health', timeout=5)
        if health_response.status_code == 200:
            print("   ✅ Health endpoint working")
        
        # Test full analysis endpoint
        print("📊 Testing full analysis endpoint...")
        analysis_response = requests.post(
            'http://localhost:8000/orchestrate/full-analysis',
            json={},
            timeout=30
        )
        
        if analysis_response.status_code == 200:
            data = analysis_response.json()
            if data.get('success'):
                print("   ✅ Full analysis working")
                print(f"   💰 Cost analysis: {'✅' if data.get('results', {}).get('cost_analysis', {}).get('success') else '❌'}")
                print(f"   🗺️ Operations analysis: {'✅' if data.get('results', {}).get('operations_analysis', {}).get('success') else '❌'}")
                print(f"   🏗️ Infrastructure analysis: {'✅' if data.get('results', {}).get('infrastructure_assessment', {}).get('success') else '❌'}")
            else:
                print(f"   ❌ Analysis failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ API request failed: {analysis_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API test failed: {e}")
    
    # Open dashboard in browser
    dashboard_path = os.path.join(os.path.dirname(__file__), 'frontend', 'dashboard.html')
    dashboard_url = f'file://{os.path.abspath(dashboard_path)}'
    
    print(f"\n🌐 Opening dashboard in browser...")
    print(f"   Dashboard URL: {dashboard_url}")
    print(f"   API Server: http://localhost:8000")
    
    try:
        webbrowser.open(dashboard_url)
        print("   ✅ Dashboard opened in browser")
    except Exception as e:
        print(f"   ⚠️ Could not open browser automatically: {e}")
        print(f"   📋 Please open this URL manually: {dashboard_url}")
    
    print("\n" + "=" * 60)
    print("🎯 Dashboard Features:")
    print("   📊 Real-time cost visualization with charts")
    print("   🗺️ Resource inventory with interactive graphs")
    print("   🏗️ Infrastructure health radar chart")
    print("   🎯 AI-generated recommendations")
    print("   🔄 Auto-refresh every 5 minutes")
    print("   📱 Responsive design for mobile/desktop")
    
    print("\n💡 Dashboard Controls:")
    print("   🔄 Click 'Refresh Data' to update with latest AWS data")
    print("   📊 Hover over charts for detailed information")
    print("   🎯 Click recommendations for more details")
    
    print("\n🚀 Your dashboard is now running!")
    print("   Keep this script running to maintain the API server")
    print("   Press Ctrl+C to stop")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down dashboard...")

if __name__ == "__main__":
    test_dashboard()
