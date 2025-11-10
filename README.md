# PDFSmart Assistant

AI-powered PDF form filling and content extraction assistant built with FastAPI, Next.js, Docling, and Google Gemini.

## 🚀 Features

### 1. Fill My PDF Assistant
- **Automatic Form Detection**: Detects form fields, checkboxes, and signature areas in PDFs
- **Natural Language Filling**: Fill forms using simple instructions like "Fill name as John, address as 123 Main St"
- **OCR Support**: Works with both digital and scanned forms
- **Smart Field Mapping**: AI-powered field recognition and value matching

### 2. Extract Anything from PDF
- **Natural Language Queries**: Extract content using queries like "Extract the price table" or "Get all email addresses"
- **Multiple Output Formats**: Export as Text, Markdown, CSV, Excel, or JSON
- **Table Detection**: Accurate table structure recognition and extraction
- **Smart Layout Analysis**: Powered by Docling for precise document understanding

### 3. Multi-OCR Engine Support
- **Tesseract**: Default free-tier OCR engine
- **EasyOCR**: Multilingual and handwritten text support
- **PaddleOCR**: Excellent for Asian languages (Thai, Chinese, Japanese, Korean)
- **RapidOCR**: Lightweight and fast processing
- **Google Vision API**: High-accuracy option (premium tier)

## 🏗️ Architecture

```
PDFSmart-Assistant/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Configuration and security
│   │   ├── services/     # Business logic
│   │   │   ├── ocr_orchestrator.py
│   │   │   ├── docling_service.py
│   │   │   ├── gemini_service.py
│   │   │   └── pdf_processor.py
│   │   └── models/       # Data models
│   └── requirements.txt
├── frontend/             # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # React components
│   │   ├── lib/          # API client
│   │   └── types/        # TypeScript types
│   └── package.json
└── docs/                 # Documentation
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Document Parser**: Docling
- **AI/LLM**: Google Gemini API
- **OCR Engines**: Tesseract, EasyOCR, PaddleOCR, RapidOCR
- **PDF Processing**: PyPDF2, pdf2image

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Styling**: TailwindCSS
- **UI Components**: Headless UI
- **HTTP Client**: Axios
- **File Upload**: React Dropzone

### Infrastructure (Recommended for Production)
- **Backend Hosting**: Render / Railway
- **Frontend Hosting**: Vercel
- **Database**: Supabase (PostgreSQL)
- **File Storage**: Cloudflare R2
- **Task Queue**: Redis + Celery (optional)

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 20+
- Tesseract OCR installed on system

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd PDFSmart-Assistant
```

2. **Set up Python virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `SECRET_KEY`: Secret key for JWT tokens

5. **Run the backend**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment**
```bash
cp .env.example .env.local
# Default API URL is http://localhost:8000
```

4. **Run the development server**
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

## 🐳 Docker Deployment

### Using Docker Compose

1. **Set environment variables**
```bash
cp backend/.env.example backend/.env
# Add your GEMINI_API_KEY and SECRET_KEY
```

2. **Build and run**
```bash
docker-compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Redis: localhost:6379

## 🔑 Getting API Keys

### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and add to `.env` as `GEMINI_API_KEY`

### Firebase (Optional - for storage/auth)
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Download service account credentials
4. Add credentials to `.env`

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Upload PDF
```bash
POST /api/upload
Content-Type: multipart/form-data
```

#### Analyze PDF
```bash
POST /api/analyze/{document_id}
```

#### Fill Form
```bash
POST /api/form/fill
{
  "document_id": "string",
  "instructions": "Fill name as John Doe, address as 123 Main St"
}
```

#### Extract Content
```bash
POST /api/extract/extract
{
  "document_id": "string",
  "extraction_query": "Extract the price table",
  "output_format": "json"
}
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Recommended Production Setup

**Frontend (Vercel)**:
1. Connect your GitHub repository to Vercel
2. Set `NEXT_PUBLIC_API_URL` to your backend URL
3. Deploy automatically on push

**Backend (Render)**:
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`

**Alternative: Railway**:
Railway provides excellent Python support with automatic deployments.

## 🔒 Security Notes

- ✅ Never commit `.env` files or credentials
- ✅ All sensitive files are excluded in `.gitignore`
- ✅ Use environment variables for all secrets
- ✅ Files are automatically deleted after 24 hours
- ✅ HTTPS enforced in production
- ✅ CORS configured for frontend origin only

## 📊 Monetization Tiers

| Tier | Documents/Month | OCR Engines | Features | Price |
|------|----------------|-------------|----------|-------|
| Free | 5 | Tesseract, EasyOCR | Basic features | $0 |
| Pro | Unlimited | + PaddleOCR, RapidOCR | Document history | $5/mo |
| Business | Unlimited | + Google Vision | API access, batch mode | $15/mo |

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

- **Documentation**: See `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/PDFSmart-Assistant/issues)
- **Email**: support@pdfsmart.com

## 🎯 Roadmap

- [ ] User authentication and accounts
- [ ] Document storage and history
- [ ] Batch processing
- [ ] API access for businesses
- [ ] Mobile app (React Native)
- [ ] Advanced form templates
- [ ] Multi-language support
- [ ] Webhook integrations

## 🙏 Acknowledgments

- **Docling** for document structure analysis
- **Google Gemini** for AI-powered understanding
- **Tesseract**, **EasyOCR**, **PaddleOCR**, **RapidOCR** for OCR capabilities
- **FastAPI** and **Next.js** communities

---

Built with ❤️ for making PDF work easier for everyone.
