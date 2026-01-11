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


# Simple lightweight fire detection using color heuristics
def detect_fire(frame: np.ndarray) -> float:
    """
    Returns a fire confidence [0.0 – 1.0] using simple color thresholding.
    """

    #Convert to HSV (better for fire color range detection)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    #Simple fire-like color range (red/orange)
    lower = np.array([0, 170, 150], dtype=np.uint8)
    upper = np.array([10, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)
    fire_pixels = np.sum(mask > 0)
    total_pixels = frame.shape[0] * frame.shape[1]

    confidence = fire_pixels / total_pixels
    return float(confidence)

# Simple lightweight smoke detection using color heuristics
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

# Wind simulation
def generate_wind() -> Tuple[float, float]:
    """
    Generates wind speed and direction randomly.
    """
    direction = random.uniform(0, 360)   # degrees
    speed = random.uniform(0, 25)        # m/s
    return speed, direction


async def weather_station(region: str, areas: list[str], nats_url: str):
    nc = await nats.connect(nats_url)

    cloud_subject = f"region.{region}.processed"

    print(f"[Station {region}] Subscribing to areas: {areas}")
    print(f"[Station {region}] Publishing to '{cloud_subject}'")

    async def msg_handler(msg):
        t_received = time.monotonic_ns()

        payload = json.loads(msg.data.decode())
        area = payload["area"]
        trace = payload["trace"]
        frame_b64 = payload["frame_bytes_b64"]

        trace["timestamps"]["edge_received"] = t_received

        # Decode image
        raw_bytes = base64.b64decode(frame_b64)
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        frame_small = cv2.resize(frame, (320, 240))

        conf_smoke = detect_smoke(frame_small)
        conf_fire = 0.00
        if conf_smoke < 0.014:
            conf_fire = detect_fire(frame_small)

        trace["timestamps"]["edge_filtered"] = time.monotonic_ns()

        wind_speed, wind_direction = generate_wind()

        # Drop if no danger
        if conf_smoke < 0.014 and conf_fire == 0.00:
            print(f"[Station {region}] Frame from {area}: CLEAN (Smoke: {conf_smoke:.5f}, Fire: {conf_fire:.5f}) -> Dropping.")
            return

        print(f"[Station {region}] Frame from {area}: SUSPICIOUS! Sending to Cloud (Smoke: {conf_smoke:.5f}, Fire: {conf_fire:.5f})")

        _, jpeg_data = cv2.imencode(".jpg", frame_small)
        jpeg_b64 = base64.b64encode(jpeg_data).decode()

        event = {
            "region": region,
            "area": area,
            "trace": trace,
            "conf_fire": conf_fire,
            "conf_smoke": conf_smoke,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "frame_jpeg_b64": jpeg_b64
        }

        trace["timestamps"]["edge_sent"] = time.monotonic_ns()

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
    nats_url = os.environ.get("NATS_URL", "nats://98.95.255.36:4222")

    # get areas associated with this region
    areas_env = os.environ.get("AREAS", "")
    areas = [a.strip() for a in areas_env.split(",") if a.strip()]

    if not areas:
        print("ERROR: No areas defined in AREAS environment variable!")
        exit(1)

    asyncio.run(weather_station(region, areas, nats_url))
