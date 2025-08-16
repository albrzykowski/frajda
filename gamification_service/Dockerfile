FROM python:3.12-slim

WORKDIR /app

COPY ./gamification_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./gamification_service/main.py .
COPY ./gamification_service/ .
COPY ./shared_config/ ./shared_config/

CMD ["python", "main.py"]