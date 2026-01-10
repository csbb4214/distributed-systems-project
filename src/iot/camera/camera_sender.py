import asyncio
import os
import time
import uuid
import json
import base64

import nats


# function to simulate the camera stream
async def camera_sender(nats_url: str, area: str, frames_dir: str, fps: int = 1):
    nc = await nats.connect(nats_url)

    subject = f"area.{area}.frame"
    frame_delay = 1 / fps

    frames = sorted([
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    print(f"Camera from area {area} streaming {len(frames)} frames to {subject}")

    while True:
        for frame_path in frames:
            with open(frame_path, "rb") as f:
                raw = f.read()

            # Create trace for time measurements
            trace = {
                "trace_id": uuid.uuid4().hex,
                "timestamps": {
                    "iot_capture": time.monotonic_ns()
                }
            }

            event = {
                "area": area,
                "trace": trace,
                "frame_bytes_b64": base64.b64encode(raw).decode()
            }

            await nc.publish(subject, json.dumps(event).encode())
            await asyncio.sleep(frame_delay)


if __name__ == "__main__":
    area = os.environ.get("AREA", "areaA")
    frames_dir = os.environ.get("FRAMES_DIR", "frames")
    fps = int(os.environ.get("FPS", "1"))
    nats_url = os.environ.get("NATS_URL", "nats://98.95.255.36:4222")

    asyncio.run(camera_sender(nats_url, area, frames_dir, fps))
