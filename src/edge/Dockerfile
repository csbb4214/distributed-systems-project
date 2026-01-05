FROM python:3.11-slim

RUN apt-get update && apt-get install -y python3-opencv && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY weather_station.py .

RUN pip install nats-py numpy

CMD ["python", "-u", "edge_station.py"]