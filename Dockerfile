# Stage 1: Build the application
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app


# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --upgrade -r requirements.txt
RUN pip install asknews
# Copy application files
COPY . /app

# Expose port
EXPOSE 8000

# Command to run the FastAPI application
CMD ["fastapi", "run", "app/main.py","--host", "0.0.0.0", "--port", "8000"]


