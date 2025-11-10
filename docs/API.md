# API Documentation - PDFSmart Assistant

Base URL: `http://localhost:8000` (development) or your deployed backend URL

## Authentication

Currently, the API is open for testing. Future versions will include:
- JWT Bearer token authentication
- API key authentication for business tier
- Rate limiting by user tier

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Document doesn't exist |
| 413 | Payload Too Large - File exceeds size limit |
| 500 | Internal Server Error |

## Endpoints

---

### 1. Health Check

Check API status and available services.

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "ocr": "available",
    "docling": "available",
    "gemini": "available"
  }
}
```

---

### 2. Upload PDF

Upload a PDF document for processing.

**Endpoint**: `POST /api/upload`

**Content-Type**: `multipart/form-data`

**Request Body**:
- `file`: PDF file (max 10MB)

**Example**:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Response**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "document.pdf",
  "file_size": 245678,
  "upload_timestamp": "2024-01-15T10:30:00.000Z",
  "expires_at": "2024-01-16T10:30:00.000Z"
}
```

**Errors**:
- 400: Invalid file type (not PDF)
- 413: File too large (>10MB)

---

### 3. Analyze PDF

Analyze PDF structure and detect form fields.

**Endpoint**: `POST /api/analyze/{document_id}`

**Path Parameters**:
- `document_id`: UUID from upload response

**Example**:
```bash
curl -X POST "http://localhost:8000/api/analyze/123e4567-e89b-12d3-a456-426614174000"
```

**Response**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_pages": 5,
  "detected_fields": [
    {
      "field_name": "Full Name",
      "field_type": "text",
      "coordinates": {
        "x": 100,
        "y": 150,
        "width": 200,
        "height": 30
      },
      "page_number": 1,
      "current_value": null
    },
    {
      "field_name": "Date",
      "field_type": "date",
      "coordinates": {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 30
      },
      "page_number": 1,
      "current_value": null
    }
  ],
  "is_scanned": false,
  "ocr_engine_used": null
}
```

**Field Types**:
- `text`: Text input field
- `checkbox`: Checkbox field
- `radio`: Radio button
- `signature`: Signature field
- `date`: Date field

---

### 4. Fill Form

Fill PDF form using natural language instructions.

**Endpoint**: `POST /api/form/fill`

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "instructions": "Fill name as John Doe, address as 123 Main Street, and today's date",
  "field_mappings": {
    "Full Name": "John Doe",
    "Address": "123 Main Street"
  }
}
```

**Parameters**:
- `document_id` (required): Document UUID
- `instructions` (required): Natural language instructions
- `field_mappings` (optional): Manual field-to-value mappings

**Example**:
```bash
curl -X POST "http://localhost:8000/api/form/fill" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "instructions": "Fill name as Jane Smith, email as jane@example.com"
  }'
```

**Response**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filled_document_url": "/api/download/123e4567_filled.pdf",
  "fields_filled": 8,
  "fields_total": 10,
  "processing_time_ms": 1234
}
```

**Errors**:
- 400: No form fields detected
- 400: Could not understand instructions
- 404: Document not found

---

### 5. Extract Content

Extract content from PDF using natural language query.

**Endpoint**: `POST /api/extract/extract`

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "extraction_query": "Extract the pricing table from page 2",
  "output_format": "json",
  "pages": [2]
}
```

**Parameters**:
- `document_id` (required): Document UUID
- `extraction_query` (required): Natural language query
- `output_format` (optional): `text` | `markdown` | `json` | `csv` (default: `text`)
- `pages` (optional): Array of page numbers (default: all pages)

**Example**:
```bash
curl -X POST "http://localhost:8000/api/extract/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "extraction_query": "Extract all email addresses",
    "output_format": "json"
  }'
```

**Response**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "extracted_content": {
    "emails": [
      "contact@example.com",
      "support@example.com"
    ]
  },
  "content_type": "application/json",
  "download_url": "/api/extract/download/123e4567",
  "processing_time_ms": 2345
}
```

---

### 6. Extract Tables

Extract all tables from PDF.

**Endpoint**: `GET /api/extract/tables/{document_id}`

**Query Parameters**:
- `pages` (optional): Comma-separated page numbers (e.g., `1,2,3`)

**Example**:
```bash
curl "http://localhost:8000/api/extract/tables/123e4567-e89b-12d3-a456-426614174000?pages=1,2"
```

**Response**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_tables": 2,
  "tables": [
    {
      "page": 1,
      "bbox": {
        "x": 50,
        "y": 100,
        "width": 500,
        "height": 200
      },
      "content": {
        "headers": ["Product", "Price", "Quantity"],
        "rows": [
          ["Widget A", "$10", "5"],
          ["Widget B", "$15", "3"]
        ]
      }
    }
  ]
}
```

---

### 7. Extract Text

Extract all text from PDF.

**Endpoint**: `GET /api/extract/text/{document_id}`

**Query Parameters**:
- `pages` (optional): Comma-separated page numbers

**Example**:
```bash
curl "http://localhost:8000/api/extract/text/123e4567-e89b-12d3-a456-426614174000"
```

**Response**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "text": "Full extracted text content from the PDF...",
  "pages_processed": 5
}
```

---

### 8. Preview Filled Form

Preview filled form fields without downloading.

**Endpoint**: `GET /api/form/preview/{document_id}`

**Example**:
```bash
curl "http://localhost:8000/api/form/preview/123e4567-e89b-12d3-a456-426614174000"
```

**Response**:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_fields": 10,
  "fields": [
    {
      "field_name": "Full Name",
      "field_type": "text",
      "current_value": "John Doe",
      "page": 1
    }
  ]
}
```

---

## Usage Examples

### Python

```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/upload', files=files)
    doc = response.json()
    document_id = doc['document_id']

# Analyze PDF
analysis = requests.post(f'http://localhost:8000/api/analyze/{document_id}')
print(f"Detected {len(analysis.json()['detected_fields'])} fields")

# Fill form
fill_request = {
    'document_id': document_id,
    'instructions': 'Fill name as John Doe, email as john@example.com'
}
result = requests.post('http://localhost:8000/api/form/fill', json=fill_request)
print(f"Filled {result.json()['fields_filled']} fields")

# Extract content
extract_request = {
    'document_id': document_id,
    'extraction_query': 'Extract all tables',
    'output_format': 'json'
}
extracted = requests.post('http://localhost:8000/api/extract/extract', json=extract_request)
print(extracted.json()['extracted_content'])
```

### JavaScript/TypeScript

```typescript
// Upload PDF
const formData = new FormData()
formData.append('file', pdfFile)

const uploadResponse = await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData
})
const { document_id } = await uploadResponse.json()

// Analyze PDF
const analysisResponse = await fetch(`http://localhost:8000/api/analyze/${document_id}`, {
  method: 'POST'
})
const analysis = await analysisResponse.json()

// Fill form
const fillResponse = await fetch('http://localhost:8000/api/form/fill', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id,
    instructions: 'Fill name as Jane Smith'
  })
})
const fillResult = await fillResponse.json()

// Extract content
const extractResponse = await fetch('http://localhost:8000/api/extract/extract', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id,
    extraction_query: 'Extract pricing table',
    output_format: 'json'
  })
})
const extracted = await extractResponse.json()
```

### cURL

```bash
# Upload
DOC_ID=$(curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@document.pdf" \
  | jq -r '.document_id')

# Analyze
curl -X POST "http://localhost:8000/api/analyze/$DOC_ID"

# Fill form
curl -X POST "http://localhost:8000/api/form/fill" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOC_ID\",
    \"instructions\": \"Fill name as Test User\"
  }"

# Extract
curl -X POST "http://localhost:8000/api/extract/extract" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOC_ID\",
    \"extraction_query\": \"Extract all text\",
    \"output_format\": \"text\"
  }"
```

---

## Rate Limits (Future Implementation)

| Tier | Requests/Hour | Documents/Month |
|------|--------------|----------------|
| Free | 60 | 5 |
| Pro | 600 | Unlimited |
| Business | Unlimited | Unlimited |

## Webhooks (Future)

For long-running operations, webhooks will be supported:

```json
{
  "webhook_url": "https://your-app.com/webhook",
  "events": ["processing.completed", "processing.failed"]
}
```

---

## Interactive Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API testing interfaces.

---

## Support

For API issues or questions:
- GitHub Issues: [Link to your repo]
- Email: support@pdfsmart.com
- Documentation: Check [ARCHITECTURE.md](./ARCHITECTURE.md)
