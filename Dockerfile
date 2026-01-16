# Use Python 3.10 slim image (TensorFlow 2.10 works well with Python 3.10)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for TensorFlow and image processing
# Also include MySQL client libraries for mysqlclient (dependency of Flask-MySQLdb)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    curl \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip (quick way)
RUN pip install --no-cache-dir uv

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies using uv pip (faster than regular pip)
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code and files
COPY . .

# Create temporary directory for file uploads
RUN mkdir -p /tmp/uploads

# Expose port (Render will use PORT env variable)
EXPOSE 5000

# Health check endpoint (using curl instead of Python requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run with Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "wsgi:application"]