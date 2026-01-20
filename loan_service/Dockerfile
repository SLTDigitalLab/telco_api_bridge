FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
# Copy loan data if exists, otherwise the script creates it
COPY loan_data.json . 

# CHANGE THIS LINE: Run the script directly
CMD ["python", "server.py"]