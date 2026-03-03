# Base image
FROM python:3.11-slim

# Set remaining commands for docker image in this directory
WORKDIR /app

# Update Ubuntu packages
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY app.py k8s.txt ./

RUN pip install fastapi uvicorn ollama chromadb


EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
