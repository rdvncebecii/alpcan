FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (OpenCV headless, SimpleITK, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları — önce pyproject.toml (Docker cache layer)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[ml,dev]"

# Uygulama kodu
# Not: ml/ dizini docker-compose.yml'de volume olarak mount edilir
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
