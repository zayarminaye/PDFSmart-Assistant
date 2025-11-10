# PDFSmart Assistant - Architecture Documentation

## System Overview

PDFSmart Assistant is a microservices-based application that provides AI-powered PDF processing capabilities through two main features:
1. **Fill My PDF Assistant** - Automated form filling using natural language
2. **Extract Anything from PDF** - Intelligent content extraction

## Architecture Diagram

```
┌─────────────────┐
│   Next.js UI    │
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────────────────────────────┐
│         FastAPI Backend                  │
│  ┌────────────────────────────────────┐ │
│  │      API Layer (Routes)            │ │
│  │  - Upload & Analysis               │ │
│  │  - Form Filling                    │ │
│  │  - Content Extraction              │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│  ┌────────────▼───────────────────────┐ │
│  │      Service Layer                 │ │
│  │  ┌──────────────────────────────┐  │ │
│  │  │   PDF Processor              │  │ │
│  │  │   (Main Orchestrator)        │  │ │
│  │  └──────┬────────────────┬──────┘  │ │
│  │         │                │          │ │
│  │  ┌──────▼──────┐  ┌─────▼────────┐ │ │
│  │  │   Docling   │  │    Gemini    │ │ │
│  │  │   Service   │  │    Service   │ │ │
│  │  └──────┬──────┘  └──────────────┘ │ │
│  │         │                           │ │
│  │  ┌──────▼──────────────────────┐   │ │
│  │  │   OCR Orchestrator          │   │ │
│  │  │  - Tesseract                │   │ │
│  │  │  - EasyOCR                  │   │ │
│  │  │  - PaddleOCR                │   │ │
│  │  │  - RapidOCR                 │   │ │
│  │  │  - Google Vision (optional) │   │ │
│  │  └─────────────────────────────┘   │ │
│  └─────────────────────────────────────┘ │
└──────────────────────────────────────────┘
         │                    │
         │                    │
    ┌────▼─────┐        ┌────▼──────┐
    │ Temp PDF │        │  Redis    │
    │ Storage  │        │  (Queue)  │
    └──────────┘        └───────────┘
```

## Component Details

### 1. Frontend (Next.js)

**Technology Stack**:
- Next.js 14 with App Router
- React 18
- TailwindCSS for styling
- TypeScript for type safety

**Key Components**:
- `FillFormTab`: Handles PDF upload and form filling workflow
- `ExtractTab`: Manages content extraction interface
- `api.ts`: Centralized API client with typed methods

**Responsibilities**:
- User interface and experience
- File upload handling
- Display of analysis results
- Preview of processed documents

### 2. Backend API Layer (FastAPI)

**Endpoints**:

#### Upload Routes (`/api`)
- `POST /upload` - Upload PDF file
- `POST /analyze/{document_id}` - Analyze PDF structure
- `GET /health` - Health check

#### Form Filling Routes (`/api/form`)
- `POST /fill` - Fill form with natural language instructions
- `GET /preview/{document_id}` - Preview filled fields

#### Extraction Routes (`/api/extract`)
- `POST /extract` - Extract content with query
- `GET /tables/{document_id}` - Extract all tables
- `GET /text/{document_id}` - Extract all text

### 3. Service Layer

#### PDF Processor Service
**Main orchestrator that coordinates all PDF operations**

Key Methods:
- `analyze_pdf()` - Comprehensive PDF analysis
- `fill_form()` - Form filling workflow
- `extract_content()` - Content extraction workflow

Workflow:
1. Receive PDF file
2. Determine if scanned or digital
3. Route to appropriate processing pipeline
4. Coordinate OCR, Docling, and Gemini services
5. Return processed results

#### Docling Service
**Handles document structure analysis**

Capabilities:
- Page layout detection
- Table structure recognition
- Form field detection
- Text block identification
- Markdown export

Integration:
- Uses Docling library for structured document understanding
- Provides bounding boxes for all detected elements
- Supports multi-page documents

#### Gemini Service
**AI-powered natural language understanding**

Use Cases:
1. **Form Filling**: Parse instructions like "Fill name as John, address as 123 Main St"
2. **Extraction Queries**: Interpret "Extract price table from page 2"
3. **Field Validation**: Validate field values match expected types
4. **Content Summarization**: Generate summaries of extracted content

#### OCR Orchestrator Service
**Manages multiple OCR engines**

Engine Selection Logic:
```python
if user_tier == BUSINESS and google_vision_available:
    return "google_vision"
elif is_handwritten:
    return "easyocr"
elif language in ["thai", "chinese", "japanese"]:
    return "paddleocr"
elif need_fast_processing:
    return "rapidocr"
else:
    return "tesseract"  # default
```

Features:
- Automatic engine selection
- Confidence scoring
- Word-level bounding boxes
- Multi-language support

## Data Flow

### Form Filling Workflow

```
1. User uploads PDF
   ↓
2. Backend saves to temporary storage
   ↓
3. Docling analyzes document structure
   ↓
4. Detect if scanned → Run OCR if needed
   ↓
5. Identify form fields (labels, types, positions)
   ↓
6. User provides natural language instructions
   ↓
7. Gemini parses instructions → field mappings
   ↓
8. Fill PDF fields with mapped values
   ↓
9. Return filled PDF to user
```

### Content Extraction Workflow

```
1. User uploads PDF
   ↓
2. Backend saves to temporary storage
   ↓
3. Docling analyzes document structure
   ↓
4. User provides extraction query
   ↓
5. Gemini interprets query → extraction parameters
   ↓
6. Determine content type (table, text, data)
   ↓
7. For scanned PDFs → Run OCR
   ↓
8. Extract target content
   ↓
9. Format output (text, markdown, CSV, JSON)
   ↓
10. Return extracted content
```

## Scalability Considerations

### Current MVP Architecture
- Stateless API design
- In-memory file processing
- No persistent storage (files deleted after 24h)
- Single server deployment

### Future Production Architecture

**Horizontal Scaling**:
- Load balancer (Nginx or cloud load balancer)
- Multiple backend instances
- Shared Redis for session state
- Distributed task queue (Celery)

**Storage**:
- Cloud object storage (S3, R2, or Firebase Storage)
- Database for user data (PostgreSQL via Supabase)
- Document metadata indexing

**Async Processing**:
- Background job queue for long-running tasks
- Webhook notifications on completion
- Progress tracking

**Caching**:
- Redis for API response caching
- CDN for static assets (Cloudflare)
- Document analysis result caching

## Security Architecture

### Authentication & Authorization
- JWT-based authentication (ready for implementation)
- API key authentication for business tier
- Rate limiting by tier

### Data Protection
- HTTPS enforced in production
- File encryption at rest (AES-256)
- Automatic file deletion after retention period
- No logging of document content

### Input Validation
- File type verification
- File size limits
- PDF structure validation
- Malware scanning (future)

## Performance Optimization

### Backend
- Async/await for I/O operations
- Connection pooling
- Response compression (gzip)
- Lazy loading of OCR engines

### Frontend
- Code splitting
- Image optimization
- Progressive loading
- Client-side caching

## Monitoring & Observability

### Metrics (Future Implementation)
- Request latency by endpoint
- OCR processing time by engine
- Document success/failure rates
- User tier usage statistics

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- No sensitive data in logs

### Error Tracking
- Exception handling at all layers
- Error responses with correlation IDs
- Client-side error boundary

## Technology Choices - Rationale

| Component | Choice | Reason |
|-----------|--------|--------|
| Backend Framework | FastAPI | High performance, async support, auto-generated docs |
| Frontend Framework | Next.js | SSR, excellent DX, Vercel integration |
| Document Parser | Docling | Best-in-class structure detection |
| LLM | Google Gemini | Free tier, good performance, easy integration |
| OCR | Multiple engines | Flexibility for different document types |
| Styling | TailwindCSS | Rapid development, consistent design |
| Deployment | Render + Vercel | Free tiers, auto-deploy, good DX |

## Future Enhancements

1. **Microservices Split**
   - Separate OCR service
   - Dedicated storage service
   - Independent scaling

2. **Real-time Processing**
   - WebSocket for progress updates
   - Streaming responses

3. **Advanced Features**
   - Batch processing API
   - Template management
   - Custom OCR training
   - Multi-document workflows

4. **AI Enhancements**
   - Fine-tuned models for specific domains
   - Active learning from user corrections
   - Confidence-based human review triggers
