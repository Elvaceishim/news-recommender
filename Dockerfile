
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PORT=8000

WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only first (to save massive space)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE $PORT

# Run the application using shell form to expand $PORT
CMD gunicorn app.api.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:$PORT
