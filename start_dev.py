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
import requests
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

def wait_for_backend_ready():
    """Wait for backend to be fully initialized and ready"""
    print("⏳ Waiting for backend services to initialize...")
    max_attempts = 20  # 20 attempts = ~40 seconds (reduced from 1 minute)
    
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get("http://localhost:8000/api/health/ready", timeout=3)  # Reduced timeout
            if response.status_code == 200:
                data = response.json()
                if data.get('ready_for_requests', False):
                    print("✅ Backend is ready for requests!")
                    return True
                else:
                    pending = data.get('pending_services', [])
                    if pending:
                        print(f"⏳ Initializing: {', '.join(pending[:2])}{'...' if len(pending) > 2 else ''} - {attempt}/{max_attempts}")
                    else:
                        print(f"⏳ Backend initializing... (attempt {attempt}/{max_attempts})")
            else:
                print(f"⏳ Backend not ready (HTTP {response.status_code}) - attempt {attempt}/{max_attempts}")
        except requests.exceptions.RequestException:
            if attempt <= 3:
                print(f"⏳ Backend starting up... (attempt {attempt}/{max_attempts})")
            elif attempt % 3 == 0:  # Every 3rd attempt after the first 3
                print(f"⏳ Still waiting for backend... (attempt {attempt}/{max_attempts})")
        
        time.sleep(2)  # Wait 2 seconds between attempts
    
    print("❌ Backend failed to become ready within timeout")
    print("💡 Backend may still be initializing. Check the logs above.")
    return False

def start_fastapi_server():
    """Start the FastAPI server with Uvicorn as subprocess"""
    print("🚀 Starting FastAPI server...")
    
    # Set environment variables
    os.environ['ENVIRONMENT'] = 'development'
    
    try:
        print("🔧 API server starting at: http://localhost:8000")
        print("📡 API endpoints:")
        print("   • POST /api/analyze - Document analysis")
        print("   • POST /api/translate - Translation service")
        print("   • POST /api/ai/clarify - AI clarification")
        print("   • GET /health - Health check")
        print("   • GET /api/health/ready - Readiness check")
        print("   • GET /docs - Interactive API documentation")
        
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
    """Start both FastAPI and React dev servers with synchronized startup"""
    print("🎯 Starting LegalSaathi Development Environment with Synchronized Startup")
    print("=" * 65)
    
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
        print("✅ FastAPI server started (PID: {})".format(fastapi_process.pid))
    else:
        print("❌ Failed to start FastAPI server")
        return
    
    # Wait for FastAPI to be ready
    print("\n🔄 Waiting for backend services to initialize...")
    if wait_for_backend_ready():
        print("🎉 Backend is fully ready!")
        
        # Now start React dev server
        print("\n🚀 Starting React development server...")
        react_process = subprocess.Popen([
            'npm', 'run', 'dev'
        ], cwd='client', shell=True)
        
        if react_process:
            processes.append(react_process)
            print("✅ React dev server started (PID: {})".format(react_process.pid))
        
        print("\n" + "=" * 65)
        print("🌟 Both services are ready!")
        print("🌐 React dev server: http://localhost:3000")
        print("🔧 FastAPI server: http://localhost:8000")
        print("📖 API documentation: http://localhost:8000/docs")
        print("🔍 Health check: http://localhost:8000/api/health/ready")
        print("\n💡 Development features:")
        print("   • Synchronized startup (no more startup errors!)")
        print("   • Hot module replacement for React")
        print("   • API proxy to FastAPI backend")
        print("   • Real-time code changes")
        print("   • TypeScript error checking")
        print("   • Backend readiness monitoring")
        print("\n🛑 Press Ctrl+C to stop both servers")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)  # Shorter delay since backend is already ready
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
                if react_process and react_process.poll() is not None:
                    print("❌ React process stopped unexpectedly")
                    break
                
                time.sleep(1)  # Check every second
                    
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"❌ Error monitoring processes: {e}")
            signal_handler(signal.SIGINT, None)
    else:
        print("❌ Backend failed to initialize properly")
        print("💡 You can still start the frontend manually with: cd client && npm run dev")
        print("   The frontend will show initialization status and wait for backend to be ready")
        
        # Keep FastAPI running even if initialization check failed
        try:
            while True:
                if fastapi_process.poll() is not None:
                    print("❌ FastAPI process stopped")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
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
    """Main function - Automatically starts both React and FastAPI with synchronization"""
    print("🚀 LegalSaathi - Synchronized Development Environment")
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
    print("🎯 Starting synchronized React frontend and FastAPI backend...")
    print("   • Backend will start first and initialize all AI services")
    print("   • Frontend will start once backend is fully ready")
    print("   • No more startup errors or 500 responses!")
    print("=" * 55)
    
    try:
        # Start both servers with synchronization
        start_both_servers()
    except KeyboardInterrupt:
        print("\n\n👋 Development servers stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()