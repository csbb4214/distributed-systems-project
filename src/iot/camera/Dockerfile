FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
RUN pip install nats-py

# Copy camera sender script
COPY camera_sender.py .

# Copy frames
COPY frames_cam01 ./frames_cam01
COPY frames_cam02 ./frames_cam02

CMD ["python", "-u", "camera_sender.py"]