# 🛡️ Phish Guard

Email phishing detection system with Flask backend, React frontend, and Celery for background processing.

## Features

- Email content analysis for phishing detection
- File upload support (.eml files)
- Real-time threat scoring
- Background processing with Celery
- Modern React UI

## Quick Start

### Local Development

1. **Start development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Access:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000

### Render Deployment

1. **Fork this repository**

2. **Deploy to Render:**
   - Login to [render.com](https://render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Click "Apply"

3. **Set up auto-deployment:**
   - Get Render API key from Account Settings
   - Add GitHub secrets: `RENDER_API_KEY` and `RENDER_SERVICE_ID`
   - Push to main branch to deploy

## Environment Setup

Copy `env.template` to `.env` and configure:

```bash
cp env.template .env
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/analyze/content` - Analyze email content
- `POST /api/analyze/file` - Analyze .eml file
- `GET /api/analysis/{task_id}` - Get analysis results

## Tech Stack

- **Backend:** Flask, Celery, Redis
- **Frontend:** React, TypeScript, Material-UI
- **Analysis:** BeautifulSoup, DNS lookup, regex patterns
- **Deployment:** Render, GitHub Actions