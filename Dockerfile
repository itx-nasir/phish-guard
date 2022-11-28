# Simple working Dockerfile
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy package files and install
COPY frontend/package*.json ./
RUN npm install --silent

# Copy source and build
COPY frontend/src ./src
COPY frontend/public ./public
RUN npm run build

# Main Python stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy frontend build
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Create directories
RUN mkdir -p /app/uploads

# Set environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Simple start script
RUN echo '#!/bin/bash\ncd /app/backend && python app.py' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 5000

CMD ["/app/start.sh"] 