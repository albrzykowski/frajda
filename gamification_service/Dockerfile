FROM python:3.12-slim

WORKDIR /app

COPY ./api_gateway ./api_gateway
COPY ./shared_config ./shared_config

WORKDIR /app/api_gateway

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app", "--worker-class", "eventlet"]