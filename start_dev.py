#!/usr/bin/env python3
"""
Development startup script for LegalSaathi React + FastAPI app
Runs both servers in a single script with proper process management
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
import threading
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies first
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn available")
    except ImportError:
        print("❌ FastAPI/Uvicorn not found. Please install requirements: uv sync (or pip install -r requirements.txt)")
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

def start_fastapi_server():
    """Start the FastAPI server with Uvicorn as subprocess"""
    print("🚀 Starting FastAPI server...")
    
    # Set environment variables
    os.environ['ENVIRONMENT'] = 'development'
    
    try:
        print("✅ FastAPI server loaded successfully")
        print("🔧 API server available at: http://localhost:8000")
        print("📡 API endpoints:")
        print("   • POST /api/analyze - Document analysis")
        print("   • POST /api/translate - Translation service")
        print("   • POST /api/ai/clarify - AI clarification")
        print("   • GET /health - Health check")
        print("   • GET /docs - Interactive API documentation")
        print("\n🛑 Press Ctrl+C to stop the API server")
        
        # Start the FastAPI app with Uvicorn as subprocess
        fastapi_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        
        return fastapi_process
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

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
    """Start both FastAPI and React dev servers"""
    print("🎯 Starting LegalSaathi Development Environment")
    print("=" * 50)
    
    # Store process references for cleanup
    processes = []
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down servers...")
        for proc in processes:
            if proc and proc.poll() is None:  # Process is still running
                try:
                    proc.terminate()
                    proc.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
                except subprocess.TimeoutExpired:
                    proc.kill()  # Force kill if it doesn't terminate gracefully
                except:
                    pass
        print("👋 Development servers stopped.")
        sys.exit(0)
    
    # Register signal handler for graceful shutdown (in main thread)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start FastAPI server as subprocess
    print("🚀 Starting FastAPI server...")
    fastapi_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info"
    ])
    
    if fastapi_process:
        processes.append(fastapi_process)
        print("✅ FastAPI server started")
    
    # Wait a moment for FastAPI to start
    time.sleep(3)
    
    # Start React dev server as subprocess
    print("🚀 Starting React development server...")
    react_process = subprocess.Popen([
        'npm', 'run', 'dev'
    ], cwd='client', shell=True)
    
    if react_process:
        processes.append(react_process)
        print("✅ React dev server started")
    
    print("\n" + "=" * 50)
    print("🌐 React dev server: http://localhost:3000")
    print("🔧 FastAPI server: http://localhost:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    print("\n💡 Development features:")
    print("   • Hot module replacement for React")
    print("   • API proxy to FastAPI backend")
    print("   • Real-time code changes")
    print("   • TypeScript error checking")
    print("\n🛑 Press Ctrl+C to stop both servers")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(5)
        try:
            webbrowser.open('http://localhost:3000')
            print("🌐 Opened browser to http://localhost:3000")
        except:
            print("💡 Please open http://localhost:3000 in your browser")
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Monitor both processes
    try:
        while True:
            # Check if processes are still running
            if fastapi_process.poll() is not None:
                print("❌ FastAPI process stopped unexpectedly")
                break
            if react_process.poll() is not None:
                print("❌ React process stopped unexpectedly")
                break
            
            time.sleep(1)  # Check every second
                
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"❌ Error monitoring processes: {e}")
        signal_handler(signal.SIGINT, None)

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
    """Main function - Automatically starts both React and FastAPI"""
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
    print("🚀 Starting both React frontend and FastAPI...")
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