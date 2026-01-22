FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install nats-py opencv-python numpy

COPY camera_sender.py .

# Copy frames
COPY frame_fire ./frame_fire
COPY frame_nofire ./frame_nofire
COPY frames_cam01 ./frames_cam01
COPY frames_cam02 ./frames_cam02

CMD ["python", "-u", "camera_sender.py"]