#!/usr/bin/env python3
"""
Development startup script for LegalSaathi React + Flask app
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies first
    try:
        import flask
        print("✅ Flask available")
    except ImportError:
        print("❌ Flask not found. Please install requirements: pip install -r requirements.txt")
        return False
    
    # Check if client directory exists
    client_dir = Path("client")
    if not client_dir.exists():
        print("❌ Client directory not found")
        return False
    
    # Check if package.json exists
    package_json = Path("client/package.json")
    if not package_json.exists():
        print("❌ Client package.json not found")
        return False
    
    print("✅ Client directory found")
    
    # Check if node_modules exists, if not try to install
    node_modules = Path("client/node_modules")
    if not node_modules.exists():
        print("📦 Installing React dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd="client", check=True, capture_output=True, shell=True)
            print("✅ React dependencies installed")
        except subprocess.CalledProcessError as e:
            print("❌ Failed to install React dependencies")
            print("   Please run: cd client && npm install")
            return False
        except FileNotFoundError:
            print("❌ npm not found. Please install Node.js and npm")
            print("   Download from: https://nodejs.org/")
            return False
    else:
        print("✅ React dependencies found")
    
    return True

def start_flask_server():
    """Start the Flask API server"""
    print("🚀 Starting Flask API server...")
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'true'
    
    try:
        # Import and run the Flask app
        from app import app
        
        print("✅ Flask API server loaded successfully")
        print("🔧 API server available at: http://localhost:5000")
        print("📡 API endpoints:")
        print("   • POST /analyze - Document analysis")
        print("   • POST /api/translate - Translation service")
        print("   • POST /api/clarify - AI clarification")
        print("   • GET /health - Health check")
        print("\n🛑 Press Ctrl+C to stop the API server")
        
        # Start the Flask app (API only)
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return False

def start_react_dev():
    """Start the React development server"""
    print("🚀 Starting React development server...")
    
    try:
        # Start dev server from client directory without changing cwd
        subprocess.run(['npm', 'run', 'dev'], cwd='client', check=True, shell=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start React dev server: {e}")
        return False
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js and npm")
        return False

def start_both_servers():
    """Start both Flask API and React dev servers"""
    import threading
    import signal
    
    print("🎯 Starting LegalSaathi Development Environment")
    print("=" * 50)
    
    # Store process references for cleanup
    processes = []
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down servers...")
        for proc in processes:
            if proc.poll() is None:  # Process is still running
                proc.terminate()
        print("👋 Development servers stopped.")
        sys.exit(0)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start Flask API server in a separate thread
    flask_thread = threading.Thread(target=start_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Wait a moment for Flask to start
    time.sleep(3)
    
    print("\n" + "=" * 50)
    print("🌐 React dev server will be available at: http://localhost:3000")
    print("🔧 Flask API server running at: http://localhost:5000")
    print("📱 React app with hot reload and API proxy")
    print("\n💡 Development features:")
    print("   • Hot module replacement for React")
    print("   • API proxy to Flask backend")
    print("   • Real-time code changes")
    print("   • TypeScript error checking")
    print("\n🛑 Press Ctrl+C to stop both servers")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(5)
        webbrowser.open('http://localhost:3000')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start React dev server as subprocess (non-blocking)
    try:
        print("🚀 Starting React development server...")
        react_process = subprocess.Popen(
            ['npm', 'run', 'dev'], 
            cwd='client',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            shell=True
        )
        processes.append(react_process)
        
        # Stream React dev server output
        for line in iter(react_process.stdout.readline, ''):
            if line:
                print(f"[React] {line.rstrip()}")
                
    except Exception as e:
        print(f"❌ Failed to start React dev server: {e}")
        return False

def check_node_availability():
    """Check if Node.js/npm is available"""
    # Check Node.js first
    try:
        node_result = subprocess.run(["node", "--version"], capture_output=True, check=True, text=True, shell=True)
        print(f"✅ Node.js {node_result.stdout.strip()} found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js not found!")
        return False
    
    # Check npm
    try:
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, check=True, text=True, shell=True)
        print(f"✅ npm {npm_result.stdout.strip()} found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm not found!")
        # Try to suggest using npx if npm is missing
        try:
            subprocess.run(["npx", "--version"], capture_output=True, check=True, shell=True)
            print("💡 Found npx, will try to use it instead")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

def main():
    """Main function - Automatically starts both React and Flask"""
    print("🚀 LegalSaathi - Starting Full Development Environment")
    print("=" * 55)
    
    # Check if Node.js is available
    print("🔍 Checking Node.js and npm availability...")
    node_available = check_node_availability()
    
    if not node_available:
        print("\n❌ Node.js/npm setup issue!")
        print("📥 You have Node.js but npm might not be in PATH")
        print("💡 Try running these commands manually:")
        print("   • node --version")
        print("   • npm --version")
        print("   • cd client && npm install")
        sys.exit(1)
    
    # Check all dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n✅ All dependencies ready!")
    print("🚀 Starting both React frontend and Flask API...")
    print("=" * 55)
    
    try:
        # Automatically start both servers
        start_both_servers()
    except KeyboardInterrupt:
        print("\n\n👋 Development servers stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()