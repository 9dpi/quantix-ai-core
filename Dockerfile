FROM python:3.11-slim

WORKDIR /app

# Cài đặt curl để Railway có thể ping kiểm tra
RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt trước để tận dụng cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ dự án
COPY . .

# Set PYTHONPATH để Python tìm thấy quantix_core trong thư mục backend
ENV PYTHONPATH=/app/backend

# Railway dùng biến môi trường PORT. Dùng shell form để $PORT được expand.
CMD uvicorn quantix_core.api.main:app --host 0.0.0.0 --port $PORT --proxy-headers
