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

    # Simple fire-like color range (red/orange)
    lower = np.array([0, 170, 150], dtype=np.uint8)
    upper = np.array([10, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)
    fire_pixels = np.sum(mask > 0)
    total_pixels = frame.shape[0] * frame.shape[1]

    confidence = fire_pixels / total_pixels
    return float(confidence)

# ---------------------------------------------------------
# Simple lightweight smoke detection using color heuristics
# ---------------------------------------------------------
def detect_smoke(frame: np.ndarray) -> float:
    """
    Returns a fire confidence [0.0 – 1.0] using simple color thresholding.
    """

    # Convert to HSV (better for fire color range detection)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Simple smoke-like color range (lightgrey/darkgrey)
    lower = np.array([0, 0, 150], dtype=np.uint8)
    upper = np.array([180, 50, 255], dtype=np.uint8)

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
# Main edge process
# ---------------------------------------------------------
async def weather_station(region: str, areas: list[str], nats_url: str):
    nc = await nats.connect(nats_url)

    cloud_subject = f"region.{region}.processed"

    print(f"[Station {region}] Subscribing to areas: {areas}")
    print(f"[Station {region}] Publishing to '{cloud_subject}'")

    async def msg_handler(msg):
        area = msg.subject.split(".")[1]
        raw_bytes = msg.data

        # Decode image
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Resize to reduce CPU & bandwidth
        frame_small = cv2.resize(frame, (320, 240))

        # Lightweight fire detection
        conf_smoke = detect_smoke(frame_small)
        conf_fire = 0.00
        if conf_smoke < 0.014:
            conf_fire = detect_fire(frame_small)

        # Wind simulation
        wind_speed, wind_direction = generate_wind()

        # If confidence is low, skip sending to cloud to reduce load
        if conf_smoke < 0.014 and conf_fire == 0.00:
            print(f"[Station {region}] Frame from {area}: no fire detected (conf_smoke={conf_smoke:.4f})")
            return

        print(f"[Station {region}] Suspicious frame from {area}! conf_fire={conf_fire:.3f}")

        # Encode frame to Base64 for safe NATS transport
        _, jpeg_data = cv2.imencode(".jpg", frame_small)
        jpeg_b64 = base64.b64encode(jpeg_data).decode()

        # Create event package
        event = {
            "region": region,
            "area": area,
            "timestamp": time.time(),
            "conf_fire": conf_fire,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "frame_jpeg_b64": jpeg_b64
        }

        await nc.publish(cloud_subject, json.dumps(event).encode())

    # Subscribe individually to each area subject part of this region
    for area in areas:
        subject = f"area.{area}.frame"
        print(f"[Station {region}] Subscribing to {subject}")
        await nc.subscribe(subject, cb=msg_handler)

    # Run indefinitely
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    region = os.environ.get("REGION", "regionA")
    nats_url = os.environ.get("NATS_URL", "nats://nats:4222")

    # get areas associated with this region
    areas_env = os.environ.get("AREAS", "")
    areas = [a.strip() for a in areas_env.split(",") if a.strip()]

    if not areas:
        print("ERROR: No areas defined in AREAS environment variable!")
        exit(1)

    asyncio.run(weather_station(region, areas, nats_url))
