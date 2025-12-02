FROM python:3.11-slim

WORKDIR /app

RUN pip install nats-py

COPY alarm_radio.py .

CMD ["python", "alarm_radio.py"]
