# Multi-stage build for React + Flask app
# Stage 1: Build React frontend
FROM node:18-slim AS frontend-build

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build the React app
RUN npm run build

# Stage 2: Build Flask backend
FROM python:3.11-slim AS backend-build

WORKDIR /app/backend

# Install system dependencies for Python
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend source code
COPY backend/ ./

# Stage 3: Final production image with nginx + Flask
FROM nginx:alpine AS production

# Install Python and system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    libmagic \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Copy built React app from frontend-build stage
COPY --from=frontend-build /app/frontend/build /usr/share/nginx/html

# Copy Flask backend from backend-build stage
COPY --from=backend-build /app/backend /app/backend

# Install Python dependencies in the final image
COPY backend/requirements.txt /app/backend/
RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt gunicorn

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Create startup script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'cd /app/backend' >> /start.sh && \
    echo 'gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 app:app &' >> /start.sh && \
    echo 'nginx -g "daemon off;"' >> /start.sh && \
    chmod +x /start.sh

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port 80 for nginx
EXPOSE 80

# Start both Flask and nginx
CMD ["/start.sh"] 