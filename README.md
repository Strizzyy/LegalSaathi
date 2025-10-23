# LegalSaathi Document Advisor

AI-powered platform for analyzing legal documents with FastAPI backend and React frontend, featuring Firebase authentication.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm
- uv (Python package manager) - `pip install uv`

### Installation

#### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd legal-saathi-document-advisor

# Run complete setup
python setup.py
```

#### Option 2: Manual Setup
```bash
# 1. Install Python dependencies
uv sync

# 2. Install frontend dependencies
cd client
npm install
cd ..

# 3. Configure environment variables (see Configuration section)
```

#### Option 3: Using Makefile
```bash
make quickstart
```

### Configuration

#### 1. Backend Environment (.env)
```bash
# Copy and edit the environment file
cp .env.example .env
```

Required environment variables:
```env
# API Keys
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=google-cloud-credentials.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# Firebase
FIREBASE_ADMIN_CREDENTIALS_PATH=firebase-admin-credentials.json
```

#### 2. Frontend Environment (client/.env.local)
```bash
# Create frontend environment file
cd client
cp .env.local.example .env.local
```

Add your Firebase configuration:
```env
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=your-app-id
```

#### 3. Firebase Setup
Follow the detailed guide in [FIREBASE_SETUP.md](FIREBASE_SETUP.md) to:
- Create a Firebase project
- Enable Email/Password authentication
- Download service account credentials
- Configure authentication settings

### Running the Application

#### Development Mode
```bash
# Terminal 1 - Start backend server
python main.py

# Terminal 2 - Start frontend development server
cd client
npm run dev
```

#### Using Makefile
```bash
make dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Available Commands

### Makefile Commands
```bash
make install          # Install all dependencies
make install-python   # Install Python dependencies only
make install-frontend # Install frontend dependencies only
make setup           # Complete setup with environment checks
make dev             # Start development servers
make test            # Run tests
make clean           # Clean build artifacts
make quickstart      # Complete setup for new developers
```

### Manual Commands
```bash
# Python dependencies
uv sync                              # Install/update Python packages
uv add package-name                  # Add new Python package

# Frontend dependencies
cd client && npm install             # Install Node.js packages
cd client && npm run dev             # Start development server
cd client && npm run build           # Build for production

# Development
python main.py                       # Start backend server
python scripts/install_frontend.py  # Install frontend dependencies only
```

## 🏗️ Project Structure

```
legal-saathi-document-advisor/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Python project configuration
├── setup.py                   # Automated setup script
├── Makefile                   # Development commands
├── .env                       # Backend environment variables
├── firebase-admin-credentials.json  # Firebase service account (not in git)
├── 
├── controllers/               # API controllers
├── models/                    # Pydantic models
├── services/                  # Business logic services
├── middleware/                # Custom middleware
├── scripts/                   # Utility scripts
├── 
├── client/                    # React frontend
│   ├── package.json          # Frontend dependencies
│   ├── .env.local            # Frontend environment (not in git)
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── contexts/         # React contexts (Auth, etc.)
│   │   ├── services/         # API services
│   │   └── firebaseConfig.ts # Firebase configuration
│   └── dist/                 # Built frontend (generated)
└── 
└── docs/                      # Documentation
    ├── FIREBASE_SETUP.md     # Firebase setup guide
    └── INSTALLATION.md       # Detailed installation guide
```

## 🔐 Authentication Features

- ✅ User registration with email/password
- ✅ User login with email/password  
- ✅ Password reset functionality
- ✅ Automatic token refresh
- ✅ Protected routes and API endpoints
- ✅ User profile management
- ✅ User-based rate limiting
- ✅ Session management

## 🛠️ Troubleshooting

### Common Issues

#### 1. Email validator error
```bash
ImportError: email-validator is not installed
```
**Solution:**
```bash
uv sync  # This will install email-validator
# Or manually: pip install email-validator
```

#### 2. Firebase configuration errors
```bash
Firebase Admin SDK not initialized
```
**Solution:**
```bash
# Run Firebase setup helper
python setup_firebase.py

# Or manually:
# 1. Follow FIREBASE_SETUP.md
# 2. Download Firebase service account credentials
# 3. Save as firebase-admin-credentials.json
```

**Note:** The application will run without Firebase if credentials are not configured, but authentication features will be disabled.

#### 3. Document AI service not configured
```bash
Authentication service not configured
```
**Solution:**
```bash
# Run Document AI setup helper
python setup_document_ai.py

# Or manually set in .env:
# DOCUMENT_AI_PROCESSOR_ID=your-processor-id
```

**Note:** The application will use basic PDF text extraction if Document AI is not configured.

#### 4. Frontend build errors
```bash
Cannot find module 'firebase/app'
```
**Solution:**
```bash
cd client
npm install
```

#### 4. Port conflicts
- Backend runs on port 8000
- Frontend runs on port 5173
- Make sure these ports are available

#### 5. CORS errors
- Add your domain to Firebase Console authorized domains
- Check CORS middleware configuration in `main.py`

### Getting Help

1. Check error messages in browser console and terminal
2. Verify all environment variables are set correctly
3. Ensure Firebase is properly configured
4. Check that all dependencies are installed
5. Review the setup guides in the `docs/` directory

## 📚 Documentation

- [Firebase Setup Guide](FIREBASE_SETUP.md) - Complete Firebase configuration
- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## 🧪 Testing

```bash
# Run Python tests
uv run pytest

# Run frontend tests (if configured)
cd client && npm test

# Run all tests
make test
```

## 🚀 Production Deployment

### Backend
1. Set environment variables in your hosting platform
2. Use production Firebase project settings
3. Configure proper CORS settings
4. Set up monitoring and logging

### Frontend
```bash
cd client
npm run build
```
Deploy the `client/dist/` directory to your static hosting service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the documentation in the `docs/` directory
3. Check existing issues in the repository
4. Create a new issue with detailed error information