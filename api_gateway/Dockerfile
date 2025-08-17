FROM python:3.12-slim

WORKDIR /app

COPY ./api_gateway ./api_gateway

COPY ./shared_config ./shared_config

RUN pip install --no-cache-dir -r api_gateway/requirements.txt

WORKDIR /app/api_gateway

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app", "--worker-class", "eventlet"]
