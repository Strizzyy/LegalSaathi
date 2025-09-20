# 🚀 LegalSaathi Universal Document Advisor

Modern AI-powered platform for analyzing legal documents with **React frontend** and **Flask API backend**.

## ✨ Features

- **🎨 Modern React UI**: 3D animations, dark theme, responsive design
- **🤖 AI-Powered Analysis**: Advanced risk assessment with confidence scoring
- **🚦 Traffic Light System**: Visual risk indicators (RED/YELLOW/GREEN)
- **🌍 Multi-Language Support**: Analysis in multiple languages
- **💬 Interactive AI Chat**: Ask questions about specific clauses
- **📊 Export Reports**: Generate PDF and Word documents
- **🎤 Voice Input**: Speech-to-text document upload
- **☁️ Google Cloud AI**: Document AI, Natural Language, Speech services

## 🏗️ Architecture

```
Frontend (React)          Backend (Flask API)
Port 3000                Port 5000
┌─────────────────┐     ┌─────────────────┐
│ • React 18      │────▶│ • Flask API     │
│ • TypeScript    │     │ • AI Services   │
│ • Tailwind CSS │     │ • Google Cloud  │
│ • Framer Motion │     │ • Document AI   │
│ • Vite Build    │     │ • Risk Analysis │
└─────────────────┘     └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** 
- **Node.js 18+** and npm

### 1. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# React dependencies  
cd client && npm install && cd ..
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Development
```bash
# Single command starts both React and Flask
python start_dev.py
```

**🌐 Access the app:**
- **React Frontend**: http://localhost:3000
- **Flask API**: http://localhost:5000

## 🔧 Development Workflow

The `start_dev.py` script automatically:
- ✅ Checks all dependencies
- ✅ Installs React packages if needed
- ✅ Starts Flask API server (port 5000)
- ✅ Starts React dev server (port 3000)
- ✅ Opens browser to React app
- ✅ Configures API proxy for seamless development

## 📁 Project Structure

```
LegalSaathi/
├── client/                    # React Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── lib/              # Utilities
│   │   └── App.tsx           # Main app
│   ├── package.json          # Frontend deps
│   └── vite.config.ts        # Build config
│
├── app.py                    # Flask API server
├── start_dev.py             # Development startup
├── risk_classifier.py       # AI risk engine
├── google_*_service.py      # Google Cloud AI
├── requirements.txt         # Python deps
└── README.md               # This file
```

## 🔌 API Endpoints

### Document Analysis
```bash
POST /analyze
Content-Type: multipart/form-data

# Response: JSON with analysis results
{
  "success": true,
  "analysis": {
    "overall_risk": {...},
    "analysis_results": [...],
    "summary": "..."
  }
}
```

### Other Endpoints
- `POST /api/translate` - Translation service
- `POST /api/clarify` - AI clarification
- `GET /health` - Health check
- `POST /api/export/pdf` - PDF export
- `POST /api/export/word` - Word export

## 🚀 Production Deployment

### Build for Production
```bash
# Build React app
cd client && npm run build

# React build output: client/dist/
```

### Deploy Options

**Option 1: Separate Deployment**
- Frontend: Deploy `client/dist/` to Vercel/Netlify
- Backend: Deploy Flask API to Heroku/Render

**Option 2: Docker**
```bash
docker build -t legalsaathi .
docker run -p 5000:5000 legalsaathi
```

## 🌍 Environment Variables

```env
# AI Services
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# Google Cloud (Optional)
GOOGLE_TRANSLATE_API_KEY=your_key
GOOGLE_CLOUD_PROJECT_ID=your_project
DOCUMENT_AI_PROCESSOR_ID=your_processor

# Flask
FLASK_ENV=production
```

## 🎯 Key Features

### React Frontend
- **Modern UI**: Dark theme with 3D animations
- **TypeScript**: Type-safe development
- **Responsive**: Works on all devices
- **Accessible**: ARIA labels, keyboard navigation
- **Fast**: Vite build system with hot reload

### Flask Backend
- **API-First**: JSON responses for all endpoints
- **AI Integration**: Multiple AI services
- **Google Cloud**: Document AI, Natural Language, Speech
- **Export**: PDF and Word report generation
- **Scalable**: Production-ready architecture

## 🛠️ Development Tips

### Hot Reload
- React changes reflect instantly
- Flask API restarts on Python changes
- Proxy handles API calls seamlessly

### Debugging
- React: Browser DevTools + React DevTools
- Flask: Python debugger + logging
- API: Test endpoints directly at localhost:5000

### Adding Features
1. **Frontend**: Add React components in `client/src/components/`
2. **Backend**: Add API routes in `app.py`
3. **Integration**: Use fetch() in React to call Flask APIs

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: Create GitHub issue
- **Documentation**: Check README files
- **Development**: Use `python start_dev.py`

## ⚠️ Disclaimer

This tool provides informational analysis only and does not constitute legal advice. Consult qualified legal professionals for specific legal matters.