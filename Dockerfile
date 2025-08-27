# MWA2 with YAML Support - Docker Container
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=dev_settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-yaml.txt /app/
RUN pip install --no-cache-dir -r requirements-yaml.txt

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/media /app/static

# Collect static files
RUN python manage.py collectstatic --noinput --settings=dev_settings || true

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Start server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001", "--settings=dev_settings"]
