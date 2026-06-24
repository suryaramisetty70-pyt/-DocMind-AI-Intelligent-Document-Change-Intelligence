# DocFinder - Intelligent Document Comparison Platform

**A professional document comparison tool with AI-powered analysis**

## 🌟 Features

- 📝 **Text Comparison** - Compare text documents with detailed diff view
- 📕 **PDF Comparison** - Extract and compare PDF content
- 📊 **Excel Comparison** - Compare spreadsheets cell-by-cell
- 📋 **CSV Comparison** - Compare CSV files instantly
- 🤖 **AI Analysis** - Powered by Groq (Llama) and Gemini
- 🔐 **Secure Authentication** - Email OTP verification
- 📊 **History Tracking** - Save and review past comparisons

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
cd docfinder

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your SMTP and API credentials

# Start backend
uvicorn docfinder.main:app --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
streamlit run docfinder/frontend/app.py --server.port 12000
```

### Environment Variables

Create a `.env` file:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./docfinder.db

# Security
SECRET_KEY=your-secret-key-here

# SMTP Email (for OTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_USE_TLS=true

# AI APIs (for semantic analysis)
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
```

## 🌐 Deployment

### Render (Recommended)

1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Set environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `SMTP_*` variables
   - `GROQ_API_KEY`
   - `GEMINI_API_KEY`
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `uvicorn docfinder.main:app --host 0.0.0.0 --port $PORT`

## 📁 Project Structure

```
docfinder/
├── main.py                 # FastAPI backend
├── auth/
│   └── utils.py            # JWT & password hashing
├── models/
│   └── models.py           # Database models
├── services/
│   ├── text_comparison.py  # Text diff engine
│   ├── pdf_comparison.py   # PDF comparison
│   ├── excel_comparison.py # Excel comparison
│   ├── csv_comparison.py   # CSV comparison
│   ├── ai_engine.py        # AI integration
│   ├── ai_integration.py   # Groq & Gemini APIs
│   ├── email_service.py    # SMTP email service
│   └── report_generator.py # Report generation
├── frontend/
│   └── app.py              # Streamlit frontend
├── database/
│   └── config.py          # Database configuration
├── test_documents/         # Sample test files
├── requirements.txt        # Python dependencies
└── .env                   # Environment variables
```

## 🔐 Authentication

DocFinder uses a secure authentication system:

1. **Registration** - Email OTP verification
2. **Login** - JWT token-based authentication
3. **Guest Mode** - Limited access without account
4. **Demo Mode** - Try all features with demo account

## 🤖 AI Integration

DocFinder uses two AI providers for semantic analysis:

### Groq (Primary - Free & Fast)
- Uses Llama 3.1 8B Instant model
- Free tier: 30 requests/minute
- Best for: Fast semantic analysis

### Gemini (Fallback)
- Google's AI model
- Best for: Complex analysis
- Rate limits apply

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/send-otp` | POST | Send OTP to email |
| `/api/auth/verify-otp` | POST | Verify OTP & register |
| `/api/register` | POST | Direct registration |
| `/api/login` | POST | User login |
| `/api/me` | GET | Get current user |
| `/api/compare/text` | POST | Compare texts |
| `/api/compare/pdf` | POST | Compare PDFs |
| `/api/compare/excel` | POST | Compare Excel files |
| `/api/compare/csv` | POST | Compare CSV files |
| `/api/history` | GET | Get comparison history |
| `/api/health` | GET | Health check |

## 🧪 Testing

Test documents are available in `test_documents/`:

- **TXT** - 12 text files
- **Excel** - 6 spreadsheet files
- **PDF** - 6 PDF documents
- **CSV** - 4 CSV files

## 📝 License

MIT License - See LICENSE file for details.

## 👨‍💻 Author

DocFinder - Built with ❤️ using FastAPI, Streamlit, and AI
