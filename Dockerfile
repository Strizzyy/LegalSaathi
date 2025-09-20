# Multi-stage build for production deployment
FROM node:18-alpine as frontend-builder

# Set working directory for frontend build
WORKDIR /app/client

# Copy frontend package files
COPY client/package*.json ./
RUN npm ci --only=production

# Copy frontend source code
COPY client/ ./

# Build the React app
RUN npm run build

# Python backend builder stage
FROM python:3.11-slim as backend-builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=backend-builder /root/.local /root/.local

# Copy React build from frontend builder
COPY --from=frontend-builder /app/client/dist ./static/dist

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]