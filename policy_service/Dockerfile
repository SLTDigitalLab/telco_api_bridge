FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (sometimes needed for building chromadb/pypdf)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run on port 8002
CMD ["python", "server.py"]