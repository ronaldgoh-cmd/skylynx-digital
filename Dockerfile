# File: Dockerfile (at repo root)
FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirement list
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY backend ./backend

# Copy env template (OPTIONAL)
# ENV variables will override these at runtime
COPY .env .env

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
