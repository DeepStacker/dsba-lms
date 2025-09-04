FROM python:3.10-slim-buster

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables for FastAPI settings
ENV APP_TITLE="AI Service API"
ENV APP_DESCRIPTION="AI-powered microservice for LMS"
ENV APP_VERSION="1.0.0"
ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT=8001

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]