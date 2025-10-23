#!/usr/bin/env python3
"""
Script to install frontend dependencies after Python dependencies are installed
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(f"✅ {command}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return None

def main():
    """Install frontend dependencies"""
    print("🚀 Installing frontend dependencies...")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    client_dir = project_root / "client"
    
    if not client_dir.exists():
        print("❌ Client directory not found!")
        sys.exit(1)
    
    # Check if npm is available
    npm_check = run_command("npm --version")
    if not npm_check:
        print("❌ npm is not installed. Please install Node.js and npm first.")
        sys.exit(1)
    
    print(f"📦 Installing packages in {client_dir}")
    
    # Install frontend dependencies
    result = run_command("npm install", cwd=client_dir)
    if not result:
        print("❌ Failed to install frontend dependencies")
        sys.exit(1)
    
    print("✅ Frontend dependencies installed successfully!")
    print("\n📋 Next steps:")
    print("1. Configure Firebase credentials")
    print("2. Start the backend: python main.py")
    print("3. Start the frontend: cd client && npm run dev")

if __name__ == "__main__":
    main()