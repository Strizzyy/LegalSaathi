@echo off
REM Development script for LegalSaathi

echo 🚀 Starting LegalSaathi Development Environment...

REM Check if build exists
if not exist "static\dist\index.html" (
    echo 📦 React build not found. Building first...
    call build.bat
)

REM Start the Flask development server
echo 🐍 Starting Flask development server...
call .venv\Scripts\activate
uv run python app.py