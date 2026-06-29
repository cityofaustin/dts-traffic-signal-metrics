FROM --platform=$BUILDPLATFORM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl/inrix_download.py .
COPY etl/inrix_payloads.py .
COPY etl/utils.py .

CMD ["python", "inrix_download.py"]
