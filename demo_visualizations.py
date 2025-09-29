#!/usr/bin/env python3
"""
Demo script to showcase the AWS Operations Command Center visualizations
"""

import sys
import os
import webbrowser
import threading
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_api_server():
    """Start the clean API server"""
    from api_server_clean import app
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

def main():
    print("🎨 AWS Operations Command Center - Visualization Demo")
    print("=" * 70)
    print("🚀 Starting enhanced dashboard with real AWS data...")
    
    # Start API server in background
    print("⚡ Starting API server...")
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait for server to start
    time.sleep(4)
    
    # Get absolute paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    desktop_dashboard = os.path.join(base_path, 'frontend', 'dashboard.html')
    mobile_dashboard = os.path.join(base_path, 'frontend', 'mobile.html')
    
    print("\n🌐 Opening dashboards...")
    
    # Open desktop dashboard
    desktop_url = f'file://{desktop_dashboard}'
    print(f"📊 Desktop Dashboard: {desktop_url}")
    
    try:
        webbrowser.open(desktop_url)
        print("   ✅ Desktop dashboard opened")
    except Exception as e:
        print(f"   ⚠️ Could not open desktop dashboard: {e}")
    
    # Wait a moment then open mobile version
    time.sleep(2)
    mobile_url = f'file://{mobile_dashboard}'
    print(f"📱 Mobile Dashboard: {mobile_url}")
    
    try:
        webbrowser.open(mobile_url)
        print("   ✅ Mobile dashboard opened")
    except Exception as e:
        print(f"   ⚠️ Could not open mobile dashboard: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 Dashboard Features Showcase:")
    print()
    print("📊 DESKTOP DASHBOARD:")
    print("   • Interactive cost breakdown charts (Chart.js)")
    print("   • Resource inventory bar charts")
    print("   • Infrastructure health radar chart")
    print("   • Real-time agent status indicators")
    print("   • AI-generated recommendations with priority")
    print("   • Auto-refresh every 5 minutes")
    print("   • Glassmorphism design with blur effects")
    print()
    print("📱 MOBILE DASHBOARD:")
    print("   • Responsive design optimized for mobile")
    print("   • Touch-friendly interface")
    print("   • Simplified metrics grid")
    print("   • Swipe-friendly card layout")
    print("   • Essential information at a glance")
    print()
    print("🎨 VISUAL ENHANCEMENTS:")
    print("   • Gradient backgrounds and glassmorphism")
    print("   • Animated status indicators and loading spinners")
    print("   • Hover effects and smooth transitions")
    print("   • Color-coded recommendations by priority")
    print("   • Professional AWS-themed color scheme")
    print()
    print("📡 REAL-TIME DATA:")
    print("   • Live AWS cost data from multiple accounts")
    print("   • Actual resource inventory (75+ resources)")
    print("   • Real infrastructure health scores")
    print("   • AI-coordinated recommendations")
    
    print("\n" + "=" * 70)
    print("🔧 API Endpoints Available:")
    print("   • GET  /health - System health check")
    print("   • GET  /health/detailed - Detailed health with AWS connectivity")
    print("   • POST /cost/analyze - Multi-account cost analysis")
    print("   • POST /operations/analyze - Resource inventory scan")
    print("   • POST /infrastructure/generate - Architecture generation")
    print("   • POST /orchestrate/full-analysis - Complete AI analysis")
    
    print("\n💡 Try These Actions:")
    print("   1. Click 'Refresh Data' to see live AWS data updates")
    print("   2. Hover over charts for detailed breakdowns")
    print("   3. Check different browser tabs for desktop vs mobile views")
    print("   4. Watch the animated status indicators")
    print("   5. Review AI recommendations with priority colors")
    
    print(f"\n🌐 API Server running at: http://localhost:8000")
    print("📊 Dashboards opened in your browser")
    print("\n🚀 Your AWS Operations Command Center is now live!")
    print("   Press Ctrl+C to stop the demo")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Demo stopped. Thanks for viewing!")

if __name__ == "__main__":
    main()
