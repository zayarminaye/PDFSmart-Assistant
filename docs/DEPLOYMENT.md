# Deployment Guide - PDFSmart Assistant

This guide covers deployment strategies for PDFSmart Assistant on various platforms.

## 🎯 Recommended Production Stack

For optimal performance and cost-effectiveness on free/low-cost tiers:

- **Frontend**: Vercel
- **Backend**: Render (or Railway)
- **Database**: Supabase (when needed)
- **File Storage**: Cloudflare R2
- **CDN**: Cloudflare (free tier)

## 📦 Pre-Deployment Checklist

### Backend
- [ ] Set all required environment variables
- [ ] Configure CORS for your frontend domain
- [ ] Set up proper error logging
- [ ] Configure file size limits
- [ ] Set SECRET_KEY to a secure random value
- [ ] Add GEMINI_API_KEY
- [ ] Configure OCR engine preferences

### Frontend
- [ ] Set NEXT_PUBLIC_API_URL to backend URL
- [ ] Configure environment-specific settings
- [ ] Optimize images and assets
- [ ] Test production build locally

### General
- [ ] Update CORS origins
- [ ] Set up monitoring/alerts
- [ ] Configure rate limiting
- [ ] Review security settings

## 🚀 Deployment Options

---

## Option 1: Vercel (Frontend) + Render (Backend)

### Deploy Backend to Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `backend` directory

3. **Configure Build Settings**
   ```
   Name: pdfsmart-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**
   ```
   GEMINI_API_KEY=your_gemini_key
   SECRET_KEY=your_secret_key
   ENVIRONMENT=production
   DEBUG=False
   BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app"]
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note your backend URL (e.g., `https://pdfsmart-backend.onrender.com`)

### Deploy Frontend to Vercel

1. **Install Vercel CLI** (optional)
   ```bash
   npm i -g vercel
   ```

2. **Deploy via GitHub Integration**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Select your GitHub repository
   - Framework Preset: Next.js
   - Root Directory: `frontend`

3. **Configure Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://pdfsmart-backend.onrender.com
   ```

4. **Deploy**
   - Click "Deploy"
   - Automatic deployments on every push to main branch

---

## Option 2: Railway (Full Stack)

Railway provides excellent support for monorepos and Python applications.

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend**
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli

   # Login
   railway login

   # Initialize project
   cd backend
   railway init

   # Add environment variables
   railway variables set GEMINI_API_KEY=your_key
   railway variables set SECRET_KEY=your_secret

   # Deploy
   railway up
   ```

3. **Deploy Frontend**
   ```bash
   cd frontend
   railway init

   # Set backend URL
   railway variables set NEXT_PUBLIC_API_URL=https://your-backend.railway.app

   # Deploy
   railway up
   ```

4. **Custom Domains** (Optional)
   - Go to Railway dashboard
   - Click on service → Settings → Domains
   - Add custom domain

---

## Option 3: Docker Deployment (Self-Hosted)

### Using Docker Compose

1. **Prepare Environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your values
   ```

2. **Build and Run**
   ```bash
   docker-compose up -d --build
   ```

3. **Services**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - Redis: localhost:6379

4. **Production Configuration**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   services:
     backend:
       restart: always
       environment:
         - ENVIRONMENT=production
         - DEBUG=False
     frontend:
       restart: always
     redis:
       restart: always
   ```

5. **Deploy**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Deploy to Cloud (GCP, AWS, Azure)

**Google Cloud Run**:
```bash
# Backend
cd backend
gcloud run deploy pdfsmart-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Frontend
cd frontend
gcloud run deploy pdfsmart-frontend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 🔧 Environment Variables Reference

### Backend (.env)

**Required**:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_random_secret_key_here
```

**Optional**:
```bash
# App Settings
APP_NAME=PDFSmart Assistant
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False

# Server
HOST=0.0.0.0
PORT=8000
BACKEND_CORS_ORIGINS=["https://your-frontend.com"]

# Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10
FILE_RETENTION_HOURS=24

# OCR
DEFAULT_OCR_ENGINE=tesseract
OCR_LANGUAGE=eng

# Redis (if using)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

---

## 🔐 Security Best Practices

### SSL/TLS
- Use HTTPS in production (automatic with Vercel/Render)
- Redirect HTTP to HTTPS
- Set secure headers

### Secrets Management
- Use platform secret managers (Render Secrets, Vercel Environment Variables)
- Never commit `.env` files
- Rotate API keys regularly

### CORS Configuration
```python
# backend/app/main.py
BACKEND_CORS_ORIGINS = [
    "https://your-production-domain.com",
    "https://www.your-production-domain.com"
]
```

### Rate Limiting
Add rate limiting middleware:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/upload")
@limiter.limit("5/hour")  # Free tier limit
async def upload_pdf():
    ...
```

---

## 📊 Monitoring & Logging

### Render
- Built-in logs: Dashboard → Service → Logs
- Metrics: CPU, Memory usage in dashboard
- Alerts: Set up via Render dashboard

### Vercel
- Analytics: Automatic with Vercel Analytics
- Logs: Vercel Dashboard → Project → Logs
- Performance: Web Vitals tracking

### Custom Monitoring (Optional)

**Sentry** (Error Tracking):
```bash
pip install sentry-sdk
```

```python
# backend/app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)
```

**LogDNA/Papertrail** (Log Aggregation):
- Add as Render add-on
- Configure log forwarding

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Render
        env:
          RENDER_DEPLOY_HOOK: ${{ secrets.RENDER_DEPLOY_HOOK }}
        run: |
          curl $RENDER_DEPLOY_HOOK

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Vercel
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        run: |
          npx vercel --prod --token=$VERCEL_TOKEN
```

---

## 🧪 Testing Before Deployment

### Backend
```bash
cd backend

# Unit tests
pytest

# Integration tests
pytest tests/integration/

# Load test
locust -f tests/load_test.py
```

### Frontend
```bash
cd frontend

# Build test
npm run build

# Start production build
npm start

# Run in different browsers
npm run test:e2e
```

---

## 📈 Scaling Strategies

### Horizontal Scaling (Render)
- Go to Dashboard → Service → Settings
- Increase "Instance Count"
- Free tier: 1 instance, Paid: Multiple instances

### Database Scaling (Supabase)
- Upgrade to Pro tier for better performance
- Enable connection pooling
- Use read replicas for heavy read workloads

### CDN (Cloudflare)
- Add your domain to Cloudflare
- Enable caching for static assets
- Configure cache rules for API responses

### Background Jobs
Add Celery for async processing:
```python
# backend/celery_app.py
from celery import Celery

celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0'
)

@celery.task
def process_large_pdf(document_id):
    # Long-running task
    pass
```

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: CORS errors in production
**Solution**: Verify BACKEND_CORS_ORIGINS includes your frontend URL

**Issue**: 413 Request Entity Too Large
**Solution**: Increase MAX_FILE_SIZE_MB and configure nginx/server limits

**Issue**: OCR not working
**Solution**: Ensure Tesseract is installed on deployment platform

**Issue**: Slow response times
**Solution**:
- Enable caching
- Optimize OCR engine selection
- Use background jobs for large files

### Platform-Specific Issues

**Render**:
- Cold starts on free tier (first request may be slow)
- 750 hours/month limit on free tier
- Add "Health Check Path": `/api/health`

**Vercel**:
- 10-second execution limit (use Edge Functions for quick responses)
- 50GB bandwidth on free tier
- Configure `maxDuration` in vercel.json for longer functions

---

## 📱 Mobile Deployment (Future)

When ready for mobile:

1. **React Native App**
   - Reuse API client from frontend
   - Deploy to App Store / Play Store

2. **Progressive Web App (PWA)**
   - Add service worker to Next.js
   - Enable offline support
   - Add to home screen capability

---

## 🎉 Post-Deployment

1. **Test All Features**
   - Upload PDF
   - Fill form
   - Extract content
   - Download results

2. **Monitor Performance**
   - Response times
   - Error rates
   - User feedback

3. **Set Up Alerts**
   - Downtime alerts
   - Error rate thresholds
   - Usage limits

4. **Update Documentation**
   - API endpoints
   - Environment setup
   - Known issues

---

Need help? Check the [Architecture Docs](./ARCHITECTURE.md) or open an issue on GitHub.
