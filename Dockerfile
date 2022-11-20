# Unified Dockerfile for both development and production
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy package files first for better caching
COPY frontend/package*.json ./
RUN npm install --silent --no-fund --no-audit

# Copy source files and build
COPY frontend/src ./src
COPY frontend/public ./public
RUN npm run build

# Main stage - Python with Flask
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Create uploads directory
RUN mkdir -p /app/uploads && chmod 755 /app/uploads

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create unified startup script
RUN echo '#!/bin/bash\n\
if [ "$MODE" = "development" ]; then\n\
  echo "Starting in DEVELOPMENT mode..."\n\
  cd /app/backend && python app.py\n\
else\n\
  echo "Starting in PRODUCTION mode..."\n\
  cd /app/backend && python app.py\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/test || exit 1

# Start the application
CMD ["/app/start.sh"] 