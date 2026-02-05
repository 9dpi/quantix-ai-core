FROM python:3.11-slim

WORKDIR /app

# Cài đặt curl để Railway có thể ping kiểm tra
RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt trước để tận dụng cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy nội dung thư mục backend vào /app
COPY backend/ .

# Explicitly set PYTHONPATH to /app so Python can find quantix_core
ENV PYTHONPATH=/app

# Railway dùng biến môi trường PORT
CMD ["sh", "-c", "uvicorn quantix_core.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
