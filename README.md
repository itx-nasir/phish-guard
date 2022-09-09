# 🛡️ Phish Guard

A comprehensive email phishing detection system built with Flask, React, and Celery for real-time email security analysis.

## ✨ Features

- **Real-time Email Analysis**: Analyze email content and files for phishing indicators
- **Advanced Detection**: Multiple analysis layers including headers, content, links, and attachments
- **Async Processing**: Background task processing with Celery for handling large files
- **Modern UI**: React-based frontend with responsive design
- **RESTful API**: Clean API endpoints for integration
- **Docker Support**: Full containerization for easy deployment
- **Security Features**: Rate limiting, CORS protection, and secure file handling

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd phish-guard
   ```

2. **Set up environment**
   ```bash
   # Make setup script executable
   chmod +x setup.sh
   
   # Run setup (development mode)
   ./setup.sh
   
   # Or for production
   ./setup.sh prod
   ```

3. **Access the application**
   - Frontend: http://localhost:3000 (dev) or http://localhost (prod)
   - Backend API: http://localhost:5000
   - Redis: localhost:6379

### Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Copy environment file (choose one)
cp env.template .env          # Use the template file
# OR cp .env.example .env     # If you have .env.example

# Edit .env file with your settings
nano .env

# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Or production environment
docker-compose -f docker-compose.prod.yml up --build -d
```

## 📁 Project Structure

```
phish-guard/
├── backend/                 # Flask API backend
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings
│   ├── services/           # Business logic services
│   │   ├── email_analyzer.py
│   │   └── file_handler.py
│   ├── utils/              # Utility functions
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   └── App.tsx        # Main app component
│   └── package.json       # Node.js dependencies
├── docker-compose.dev.yml  # Development environment
├── docker-compose.prod.yml # Production environment
└── setup.sh               # Setup script
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `env.template` (or `.env.example` if available):

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
FLASK_ENV=development

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
API_RATE_LIMIT=100 per hour
```

### Key Features Configuration

- **File Upload Limits**: 16MB max file size
- **Supported Formats**: .eml email files
- **Rate Limiting**: 100 requests per hour by default
- **Phishing Threshold**: 0.7 (configurable)

## 📚 API Documentation

### Health Check
```http
GET /api/health
```

### Analyze Email Content
```http
POST /api/analyze/content
Content-Type: application/json

{
  "content": "Raw email content here..."
}
```

### Analyze Email File
```http
POST /api/analyze/file
Content-Type: multipart/form-data

file: <email.eml>
```

### Get Analysis Results
```http
GET /api/analysis/{task_id}
```

### Response Format

```json
{
  "status": "completed",
  "result": {
    "threat_score": 0.8,
    "risk_level": "high",
    "header_analysis": {...},
    "content_analysis": {...},
    "link_analysis": {...},
    "attachment_analysis": {...},
    "recommendations": [...]
  }
}
```

## 🛠️ Development

### Running Tests

```bash
# Backend tests
docker exec -it phish-guard-backend-1 python -m pytest

# Frontend tests
docker exec -it phish-guard-frontend-1 npm test
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f backend
```

### Development Workflow

1. **Code Changes**: Edit files in your local directory
2. **Hot Reload**: Frontend automatically reloads, backend restarts on changes
3. **Debugging**: Use Docker logs and Flask debug mode
4. **Testing**: Run tests in containers

## 🏗️ Architecture

### Backend Components

- **Flask API**: RESTful endpoints for email analysis
- **Celery Workers**: Async processing of analysis tasks
- **Redis**: Message broker and result storage
- **Email Analyzer**: Core analysis engine

### Frontend Components

- **React App**: Modern SPA with TypeScript
- **Analysis Dashboard**: Upload and view results
- **Result Visualization**: Interactive threat analysis display

### Security Features

- **Input Validation**: Strict file type and size checking
- **Rate Limiting**: API protection against abuse
- **CORS Protection**: Controlled cross-origin access
- **Error Handling**: Comprehensive error management
- **Secure File Handling**: Temporary file cleanup

## 🔒 Security Considerations

- Files are processed in isolated containers
- Temporary files are automatically cleaned up
- Rate limiting prevents API abuse
- Input validation prevents malicious uploads
- No persistent storage of sensitive data

## 🚀 Deployment

### Production Deployment

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Deploy with Docker**
   ```bash
   ./setup.sh prod
   ```

3. **Environment Considerations**
   - Use strong SECRET_KEY
   - Configure proper CORS_ORIGINS
   - Set up monitoring and logging
   - Consider using external Redis for scaling

### Scaling

- **Horizontal Scaling**: Add more Celery workers
- **Load Balancing**: Use nginx or cloud load balancers
- **Database**: Consider PostgreSQL for persistent data
- **Monitoring**: Implement health checks and metrics

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using ports
   lsof -i :3000
   lsof -i :5000
   lsof -i :6379
   ```

2. **Docker Build Issues**
   ```bash
   # Clean rebuild
   docker-compose down
   docker system prune -f
   docker-compose up --build
   ```

3. **Celery Worker Issues**
   ```bash
   # Check worker logs
   docker-compose logs celery_worker
   ```

### Health Checks

```bash
# Backend health
curl http://localhost:5000/api/health

# Redis health
docker exec phish-guard-redis-1 redis-cli ping

# Service status
docker-compose ps
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔄 Recent Improvements

### Bug Fixes ✅

- **Fixed Docker casing warnings** in Dockerfiles (FROM/AS keywords)
- **Updated Celery configuration** to use new format (removed deprecated CELERY_ prefix)
- **Fixed security warning** for Celery worker running as root
- **Removed obsolete version** from docker-compose files
- **Fixed import issues** and circular dependencies
- **Improved error handling** throughout the application

### Enhancements 🎯

- **Enhanced security** with proper user permissions in containers
- **Improved logging** with structured logging configuration
- **Better error responses** with detailed error messages
- **File size validation** and proper cleanup
- **Rate limiting** implementation
- **Health check improvements** with version information
- **Comprehensive .dockerignore** files for better build performance

### New Features 🌟

- **Production-ready** Docker configuration
- **Automated setup script** with health checks
- **Celery Beat scheduler** for periodic tasks
- **Redis persistence** configuration
- **Comprehensive documentation** and troubleshooting guide 