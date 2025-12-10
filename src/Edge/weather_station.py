import asyncio
import base64
import json
import os
import random
import time
from typing import Tuple

import cv2
import numpy as np
import nats


# ---------------------------------------------------------
# Simple lightweight fire detection using color heuristics
# ---------------------------------------------------------
def detect_fire(frame: np.ndarray) -> float:
    """
    Returns a fire confidence [0.0 – 1.0] using simple color thresholding.
    """

    # Convert to HSV (better for fire color range detection)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower = np.array([0, 120, 120])     # reddish/orange lower bound
    upper = np.array([30, 255, 255])    # reddish/orange upper bound

    mask = cv2.inRange(hsv, lower, upper)
    fire_pixels = np.sum(mask > 0)
    total_pixels = frame.shape[0] * frame.shape[1]

    confidence = fire_pixels / total_pixels

    return float(confidence)


# ---------------------------------------------------------
# Wind simulation
# ---------------------------------------------------------
def generate_wind() -> Tuple[float, float]:
    """
    Generates wind speed and direction randomly.
    """
    direction = random.uniform(0, 360)   # degrees
    speed = random.uniform(0, 25)        # m/s
    return speed, direction


# ---------------------------------------------------------
# Main Edge process
# ---------------------------------------------------------
async def weather_station(station_id: str, area: str):
    nc = await nats.connect("nats://nats:4222")

    camera_subject = f"camera.*.frame"
    cloud_subject = f"weather.{station_id}.processed"

    print(f"[WEATHER {station_id}] Listening for camera frames on '{camera_subject}'")
    print(f"[WEATHER {station_id}] Sending processed data to '{cloud_subject}'")

    async def msg_handler(msg):
        camera_id = msg.subject.split(".")[1]
        raw_bytes = msg.data

        # Decode image
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Resize to reduce CPU & bandwidth
        frame_small = cv2.resize(frame, (320, 240))

        # Lightweight fire detection
        conf = detect_fire(frame_small)

        # Wind data simulation
        wind_speed, wind_direction = generate_wind()

        # If confidence is low, skip sending to cloud to reduce load
        if conf < 0.01:
            print(f"[WEATHER {station_id}] Frame from {camera_id}: no fire detected (conf={conf:.4f})")
            return

        print(f"[WEATHER {station_id}] 🔥 Suspicious frame from {camera_id}! conf={conf:.3f}")

        # Encode frame to Base64 for safe NATS transport
        _, jpeg_data = cv2.imencode(".jpg", frame_small)
        jpeg_b64 = base64.b64encode(jpeg_data).decode()

        # Create event package
        event = {
            "station_id": station_id,
            "area": area,
            "camera_id": camera_id,
            "timestamp": time.time(),
            "fire_confidence": conf,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "frame_jpeg_b64": jpeg_b64
        }

        await nc.publish(cloud_subject, json.dumps(event).encode())

    await nc.subscribe(camera_subject, cb=msg_handler)

    # Run indefinitely
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    station_id = os.environ.get("STATION_ID", "edge01")
    area = os.environ.get("EDGE_AREA", "areaA")

    asyncio.run(weather_station(station_id, area))
