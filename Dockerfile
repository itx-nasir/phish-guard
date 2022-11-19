# Multi-stage build for React frontend and Flask backend

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --silent --no-fund --no-audit
COPY frontend/ ./

# Build the frontend for production
RUN npm run build

# Stage 2: Setup Python backend
FROM python:3.11-slim AS backend

# Install system dependencies for Flask and curl for healthcheck
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend application
COPY backend/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Create uploads directory
RUN mkdir -p /app/uploads && chmod 755 /app/uploads

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV NODE_ENV=production

# Create startup script
RUN echo '#!/bin/bash\ncd /app/backend && gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app' > /app/start.sh
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/test || exit 1

# Start the application
CMD ["/app/start.sh"] 