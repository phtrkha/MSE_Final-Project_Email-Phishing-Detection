# Dockerfile cho Flask
FROM python:3.9

# Đặt thư mục làm việc trong container
WORKDIR /app

# Copy file yêu cầu vào container và cài đặt các thư viện
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Expose cổng 5000 để Flask có thể truy cập từ bên ngoài
EXPOSE 5000

# Chạy ứng dụng Flask
CMD ["python", "backend/app.py"]
