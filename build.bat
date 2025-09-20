@echo off
REM Build script for LegalSaathi React + Flask application

echo 🚀 Building LegalSaathi Application...

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: app.py not found. Please run this script from the project root.
    exit /b 1
)

REM Build React frontend
echo 📦 Building React frontend...
cd client

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo 📥 Installing frontend dependencies...
    npm install
)

REM Build the React app
echo 🔨 Building React app...
npm run build

cd ..

REM React build stays in client/dist for separate serving
echo ✅ React build completed in client/dist/

REM Install Python dependencies if needed
if not exist ".venv" (
    echo 🐍 Creating Python virtual environment...
    python -m venv .venv
)

echo 📥 Installing Python dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt

echo ✅ Build completed successfully!
echo.
echo 🎯 Next steps:
echo    • Full development: python start_dev.py
echo    • API only: python run_api.py
echo    • React only: cd client ^&^& npm run dev
echo.
echo 🌐 Development servers:
echo    • React dev: http://localhost:3000
echo    • Flask API: http://localhost:5000