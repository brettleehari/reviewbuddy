FROM python:3.11-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy analysis package
COPY packages/analysis /app/packages/analysis

# Copy API code
COPY apps/api/ /app/

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
