FROM python:3.11-slim

WORKDIR /app

RUN pip install nats-py
RUN mkdir -p /app/data

COPY alarm_radio.py .

CMD ["python", "-u", "alarm_radio.py"]
