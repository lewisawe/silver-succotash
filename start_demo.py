#!/usr/bin/env python3
"""
Start demo server with live dashboard
"""
import sys
sys.path.append('.')
from api_server import app
import webbrowser
import threading
import time

def open_browser():
    """Open browser after server starts"""
    time.sleep(2)
    webbrowser.open('http://localhost:8000/frontend/dashboard.html')

if __name__ == "__main__":
    print("🚀 Starting AWS Operations Command Center Demo")
    print("=" * 50)
    print("🌐 Web Dashboard: http://localhost:8000/frontend/dashboard.html")
    print("🔗 API Endpoints: http://localhost:8000/")
    print("=" * 50)
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start server
    app.run(host='0.0.0.0', port=8000, debug=False)
