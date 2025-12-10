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


def detect_fire(frame: np.ndarray) -> float:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 120, 120])
    upper = np.array([30, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    fire_pixels = np.sum(mask > 0)
    total_pixels = frame.shape[0] * frame.shape[1]
    return float(fire_pixels / total_pixels)


def generate_wind() -> Tuple[float, float]:
    direction = random.uniform(0, 360)
    speed = random.uniform(0, 25)
    return speed, direction


async def weather_station(nats_url: str, region: str, areas: list[str]):
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

        # Resize to reduce compute
        frame_small = cv2.resize(frame, (320, 240))

        # Fire detection
        conf = detect_fire(frame_small)

        # Wind simulation
        wind_speed, wind_direction = generate_wind()

        if conf < 0.01:
            print(f"[Station {region}] Frame from {area}: no fire (conf={conf:.4f})")
            return

        print(f"[Station {region}] Suspicious frame in {area}! conf={conf:.3f}")

        # Prepare frame
        _, jpeg_data = cv2.imencode(".jpg", frame_small)
        jpeg_b64 = base64.b64encode(jpeg_data).decode()

        # Package event
        event = {
            "region": region,
            "area": area,
            "timestamp": time.time(),
            "fire_confidence": conf,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "frame_jpeg_b64": jpeg_b64,
        }

        await nc.publish(cloud_subject, json.dumps(event).encode())

    # Subscribe individually to each area subject part of this region
    for area in areas:
        subject = f"area.{area}.frame"
        print(f"[Station {region}] Subscribing to {subject}")
        await nc.subscribe(subject, cb=msg_handler)

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

    asyncio.run(weather_station(nats_url, region, areas))
