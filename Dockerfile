FROM python:3.11-slim

WORKDIR /app

# Cài đặt curl để Railway có thể ping kiểm tra
RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt trước để tận dụng cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy nội dung thư mục backend vào /app
COPY backend/ .

# Railway dùng biến môi trường PORT. 
# CMD dạng shell để $PORT được thay thế chính xác.
# Ta bind vào 0.0.0.0 để có thể nhận traffic từ internet.
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT
