# DocFinder - Intelligent Document Difference Finder

An AI-powered document comparison platform that identifies additions, deletions, modifications, and semantic changes across multiple document formats.

## Features

### Document Comparison
- **Text Files** (TXT) - Character, word, sentence, and paragraph level comparison
- **PDF Files** - Text and scanned PDF comparison with OCR support
- **Excel Files** (XLSX, XLS) - Sheet, row, column, and cell comparison
- **CSV Files** - Row and column comparison

### AI-Powered Analysis
- Semantic similarity detection using sentence transformers
- Paraphrase identification
- Change importance classification (Critical, High, Medium, Low)
- Human-readable change summaries

### Authentication
- User registration and login
- JWT-based authentication
- Admin dashboard with user management

### Reporting
- PDF report generation
- Excel report generation
- Detailed comparison statistics

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip

### Installation

1. Navigate to the docfinder directory:
```bash
cd docfinder
```

2. Make scripts executable:
```bash
chmod +x start.sh stop.sh
```

3. Start the application:
```bash
./start.sh
```

4. Access the application:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8001
- API Documentation: http://localhost:8001/docs

### Default Admin Credentials
- Username: `admin`
- Password: `admin123`

## Project Structure

```
docfinder/
├── auth/                 # Authentication utilities
│   └── utils.py         # Password hashing, JWT token handling
├── database/            # Database configuration
│   └── config.py        # SQLAlchemy async setup
├── models/              # Database models
│   └── models.py        # User, Comparison, Report models
├── services/            # Core business logic
│   ├── text_comparison.py   # Text comparison engine
│   ├── pdf_comparison.py    # PDF comparison engine
│   ├── excel_comparison.py  # Excel/CSV comparison engine
│   ├── ocr_engine.py        # OCR for scanned documents
│   ├── ai_engine.py        # AI semantic analysis
│   └── report_generator.py  # PDF/Excel report generation
├── frontend/            # Streamlit frontend
│   └── app.py          # Main Streamlit application
├── main.py             # FastAPI backend application
├── requirements.txt    # Python dependencies
├── start.sh           # Startup script
└── stop.sh            # Stop script
```

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user

### Comparison
- `POST /api/compare/text` - Compare text inputs
- `POST /api/compare/pdf` - Compare PDF files
- `POST /api/compare/excel` - Compare Excel files
- `POST /api/compare/csv` - Compare CSV files

### Reports
- `POST /api/report/pdf/{id}` - Generate PDF report
- `POST /api/report/excel/{id}` - Generate Excel report

### History
- `GET /api/history` - Get user's comparison history

### Admin
- `GET /api/admin/stats` - Get system statistics
- `GET /api/admin/users` - List all users

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **aiosqlite** - Async SQLite support

### Frontend
- **Streamlit** - Data science web application framework

### Document Processing
- **PyPDF2** - PDF text extraction
- **pdfplumber** - Advanced PDF processing
- **openpyxl** - Excel file handling
- **pandas** - Data analysis

### AI/NLP
- **sentence-transformers** - Semantic similarity
- **NLTK** - Natural language processing
- **spacy** - Advanced NLP

### OCR
- **pytesseract** - Tesseract OCR Python wrapper
- **easyocr** - Deep learning based OCR

### Reports
- **reportlab** - PDF generation

## Usage Examples

### Compare Text
1. Navigate to the Compare page
2. Select "Text" comparison type
3. Paste original text in left box
4. Paste modified text in right box
5. Select comparison level (word/sentence/paragraph/character)
6. Click "Compare Text"

### Compare PDFs
1. Navigate to the Compare page
2. Select "PDF" comparison type
3. Upload original PDF
4. Upload modified PDF
5. Enable OCR if PDFs are scanned
6. Click "Compare PDFs"

### Generate Report
1. After comparison, view results
2. Use the report generation feature
3. Download PDF or Excel report

## Development

### Running Backend Only
```bash
uvicorn docfinder.main:app --reload --port 8001
```

### Running Frontend Only
```bash
streamlit run docfinder/frontend/app.py --server.port 8501
```

### Environment Variables
- `DATABASE_URL` - Database connection string (default: SQLite)
- `SECRET_KEY` - JWT secret key
- `API_BASE_URL` - Backend API URL for frontend

## License

MIT License