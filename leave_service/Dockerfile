FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY data.json . 

# CHANGE THIS LINE: Run the script directly
CMD ["python", "server.py"]