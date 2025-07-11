# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libsndfile1 \
    && apt-get clean

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose FastAPI port
EXPOSE 8080

# Run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
