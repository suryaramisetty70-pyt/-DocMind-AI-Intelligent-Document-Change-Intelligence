# ScholarSync - AI-Powered Multi-Agent Platform

**A professional learning, career guidance, and document intelligence tool with 7 specialized AI agents.**

## 🚀 Features

- 📚 **Teaching Agent** - Personalized AI tutor for learning and practice.
- 💼 **Career & Job Training Agent** - Resume building and interview prep.
- 🏥 **Medical Knowledge Agent** - Health and wellness information.
- 🌱 **Plant Intelligence Agent** - Visual disease detection for plants.
- 📈 **Trading & Finance Agent** - Economic guidance and markets.
- ⚖️ **Law & Police Agent** - Legal procedures and knowledge.
- 📄 **Document Intelligence Agent** - Compare text, PDF, Excel, and CSV with semantic diffs.
- 👁️ **Gemini Vision Integration** - Upload images directly to specific agents for multimodal analysis.
- 🔒 **Secure Authentication** - Email OTP verification and JWT sessions.

## ⚡ Quick Start

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

# AI APIs
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
```

## 🧠 AI Integration

ScholarSync uses advanced AI providers for conversational intelligence and semantic analysis:

### Groq (Primary Text Engine)
- Uses Llama 3.1 8B Instant model
- Fast reasoning for core text-based agents

### Google Gemini (Vision Engine)
- Gemini 1.5 Pro is used for `/api/agents/chat_multimodal`
- Processes image uploads (e.g. sick plants, medical scans)

## 📁 Project Structure
```
docfinder/
├── main.py                 # FastAPI backend & Agent router
├── models/
│   └── models.py           # Database models (User, AgentConversation, Message, etc.)
├── services/
│   ├── multi_agent.py      # Multi-Agent logic & hidden rules
│   ├── ai_integration.py   # Groq & Gemini APIs
│   └── ...                 # Document diff engines
├── docfinder_frontend/
│   ├── dashboard.html      # The ScholarSync Hub
│   ├── agent_chat.html     # Universal Multi-Modal Chat UI
│   └── ...
└── requirements.txt        # Python dependencies
```

## 📄 License
MIT License - See LICENSE file for details.
