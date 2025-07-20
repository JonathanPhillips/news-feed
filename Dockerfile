# Use Python slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY setup_preferences.py .
COPY tests/ ./tests/
COPY pytest.ini .

# Create directory for database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/news_feed.db

# Run the application
CMD ["python", "backend/main.py"]