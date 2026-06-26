FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI server
COPY main.py .

# Copy the bi_copilot package from Day 9
# (deploy.sh copies it here before building the image)
COPY bi_copilot/ ./bi_copilot/

# Copy env config
COPY .env .

ENV PORT=8080

EXPOSE 8080

CMD ["python", "main.py"]
