FROM python:3.12-slim

WORKDIR /app

COPY ./gamification_service/ ./gamification_service/
COPY ./shared_config/ ./shared_config/

RUN pip install --no-cache-dir -r gamification_service/requirements.txt

WORKDIR /app/gamification_service

CMD ["python", "main.py"]