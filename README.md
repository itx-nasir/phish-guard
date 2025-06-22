# 🛡️ PhishGuard

Advanced email phishing detection system with comprehensive analysis and historical tracking.

## ✨ Features

- **Email Analysis Engine** - Upload `.eml` files or paste email content
- **Multi-layer Detection** - Analyzes headers, content, links, and attachments
- **VirusTotal Integration** - Real-time threat intelligence for URLs, domains, and IPs
- **Threat Scoring** - Returns threat score (0-100%) and risk level (Low/Medium/High)
- **Background Processing** - Fast response with Celery + Redis
- **Batch Processing** - Analyze multiple emails simultaneously (up to 10 files)
- **📊 Historical Dashboard** - Track analysis history with interactive charts and statistics
- **📈 Trend Analysis** - Visualize threat patterns over time
- **📋 Data Export** - Export analysis results in CSV or JSON format
- **🔍 Advanced Filtering** - Filter history by risk level, date range, and more

## 📊 Historical Dashboard Features

The new Historical Analysis Dashboard provides comprehensive insights:

- **📈 Interactive Charts** - Line charts for trends, pie charts for risk distribution
- **📋 Data Tables** - Paginated history with sorting and filtering
- **📤 Export Options** - Download data in CSV or JSON format
- **🔍 Advanced Filters** - Filter by risk level, date range, analysis type
- **📊 Statistics Cards** - Quick overview of total analyses and risk distribution
- **📅 Trend Analysis** - Visualize patterns over 7, 30, or 90-day periods

## Quick Start

```bash
# Clone and start
git clone https://github.com/your-username/phish-guard.git
cd phish-guard
cp env.template .env

# Configure VirusTotal API (optional but recommended)
# Get your free API key from https://www.virustotal.com/gui/join-us
# Add it to .env: VIRUSTOTAL_API_KEY=your-api-key-here

docker-compose up --build
```

**Access:** 
- **Main Dashboard:** http://localhost:5000 (Email analysis)
- **Historical Dashboard:** http://localhost:5000/history (Statistics & trends)

## 🧪 Test it

1. **Single File Analysis**
   - Upload `test-sample.eml` (included) or paste email content
   - Get detailed analysis with threat score and recommendations

2. **Batch Analysis**
   - Select multiple `.eml` files (up to 10) or drag-and-drop them
   - View batch processing progress and individual results
   - Download combined analysis report
   - Access detailed analysis for each file

3. **Historical Dashboard** - Visit `/history` to see analysis trends and statistics

4. **API Testing**:
```bash
# Single file analysis
curl -X POST \
  -F "file=@test-sample.eml" \
  http://localhost:5000/api/analyze/file

# Batch analysis
curl -X POST \
  -F "files[]=@test-sample.eml" \
  -F "files[]=@test-phishing.eml" \
  http://localhost:5000/api/analyze/batch

# Content analysis
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content":"From: suspicious@phishing.com\nSubject: URGENT Account Suspended"}' \
  http://localhost:5000/api/analyze/content
```

## 🔌 API Endpoints

### Analysis
- `POST /api/analyze/content` - Analyze email text
- `POST /api/analyze/file` - Upload single .eml file
- `POST /api/analyze/batch` - Upload multiple .eml files (max 10)
- `GET /api/analysis/{task_id}` - Get analysis results

### Historical Data
- `GET /api/history` - Get paginated analysis history (with filters)
- `GET /api/statistics` - Get overall statistics summary
- `GET /api/trends?days=30` - Get trend data for charts
- `GET /api/export?format=csv` - Export data (CSV or JSON)
- `GET /api/history/{task_id}` - Get detailed historical analysis

### System
- `GET /api/health` - Health check
- `GET /api/test` - API status test

## 🔧 VirusTotal Integration

PhishGuard now includes real-time threat intelligence via VirusTotal API:

### Setup:
1. Get a free API key from [VirusTotal](https://www.virustotal.com/gui/join-us)
2. Add to your `.env` file: `VIRUSTOTAL_API_KEY=your-api-key-here`
3. Restart the application

### Features:
- **🔗 URL Analysis** - Checks all URLs found in emails against VirusTotal database
- **📧 Sender Domain Analysis** - Validates sender domain reputation and history
- **🌐 IP Address Scanning** - Analyzes IPs from email content AND routing headers
- **📎 Attachment Hash Analysis** - SHA256 hash checking of all email attachments
- **🛣️ Email Routing Analysis** - Checks reputation of servers that handled the email
- **⚡ Real-time Results** - Shows malicious/suspicious indicators in analysis results
- **🎯 Enhanced Scoring** - Comprehensive threat intelligence improves detection accuracy

### Dashboard Display:
- **🔴 Malicious Indicators** - Critical threats highlighted in red
- **🟠 Suspicious Indicators** - Potential threats shown in orange
- **📊 Detailed Scan Results** - Detection counts from multiple security engines
- **📧 Sender Analysis** - Domain reputation and creation date
- **📎 Attachment Reports** - File hash analysis and malware detection
- **🌐 IP Geolocation** - Country and network owner information
- **🛣️ Email Path Analysis** - Routing server reputation checks

*Note: VirusTotal integration is optional. The system works without an API key but provides enhanced detection with it.*

## 🛠️ Tech Stack

- **Backend:** Flask + Celery + Redis + SQLAlchemy
- **Frontend:** React + Material-UI + Recharts
- **Database:** SQLite (configurable to PostgreSQL/MySQL)
- **Analysis:** Pattern matching, domain checking, header validation, VirusTotal threat intelligence
- **Charts:** Interactive data visualization with trend analysis
- **Export:** CSV and JSON data export capabilities

## 🚀 Planned Features

### 🔥 High Priority
- **Email Chain Analysis** - Analyze forwarding patterns and email threads
- **Custom Rules Engine** - User-defined detection rules and scoring

### 🌟 Medium Priority
- **API Integration Suite** - REST API with webhook notifications
- **Advanced Reporting** - PDF report generation and email alerts
- **Machine Learning Enhancement** - ML models for pattern recognition
- **Real-time Dashboard Updates** - WebSocket integration for live data

### 💡 Nice-to-Have
- **Browser Extension** - Real-time analysis for Gmail/Outlook
- **Mobile Application** - iOS/Android app with push notifications
- **Team Collaboration** - Multi-user support with role-based access
- **SIEM Integration** - Microsoft 365, Google Workspace, and security platform plugins

## 🔧 Troubleshooting

```bash
# Check logs
docker-compose logs -f

# Check specific service
docker-compose logs backend
docker-compose logs celery_worker

# Restart services
docker-compose restart

# Clean rebuild (removes database)
docker-compose down -v && docker-compose up --build

# View database (SQLite)
docker-compose exec app sqlite3 /app/phishguard.db
```

## 📊 Database Schema

The application automatically creates the following tables:
- `analysis_results` - Stores detailed analysis results
- `analysis_statistics` - Daily aggregated statistics for trends

Data is automatically cleaned up (default: 90 days retention).