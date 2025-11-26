FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/
RUN ls

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8022

# Start server with migrations
CMD python manage.py migrate --noinput && gunicorn slotlist_backend.wsgi:application --bind 0.0.0.0:8022
