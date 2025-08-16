FROM python:3.12-slim

WORKDIR /app

COPY ./api_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./api_gateway/main.py .
COPY ./shared_config/ ./shared_config/

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]