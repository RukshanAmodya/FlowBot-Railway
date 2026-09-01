FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# Set non-interactive and environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HEADLESS=true \
    PORT=8000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser dependencies
RUN playwright install chromium

# Copy application source code
COPY . .

# Create essential runtime directories
RUN mkdir -p /app/browser_profile /app/generated /app/logs /app/screenshots

# Expose Railway assigned port
EXPOSE 8000

# Start FastAPI application using dynamic port
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
