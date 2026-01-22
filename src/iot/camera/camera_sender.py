import asyncio
import os
import time
import uuid
import json
import base64

import nats
import cv2
import numpy as np


# function to simulate the camera stream
async def camera_sender(nats_url: str, area: str, frames_dir: str, fps: float = 1.0):
    try:
        nc = await nats.connect(nats_url)
    except Exception as e:
        print(f"Could not connect to NATS at {nats_url}: {e}")
        return

    subject = f"area.{area}.frame"
    frame_delay = 1 / fps

    # Collect images
    frames = sorted([
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    print(f"Camera from area {area} streaming {len(frames)} frames to {subject}")
    print("Press 'q' in the image window to stop the stream.")

    try:
        while True:
            for frame_path in frames:
                with open(frame_path, "rb") as f:
                    raw = f.read()

                # --- NEW: VISUALIZATION LOGIC ---
                # 1. Convert raw bytes to a numpy array
                nparr = np.frombuffer(raw, np.uint8)

                # 2. Decode the numpy array into an OpenCV image
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # 3. Show the image.
                # The first argument is the window title. As long as the title
                # is the same, it updates the existing window instead of opening a new one.
                cv2.imshow(f"Live Feed: {area}", img)

                # 4. Wait 1ms for the GUI to update.
                # This is required for the image to actually render.
                # We also check if the user pressed 'q' to quit.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Stop signal received.")
                    return
                # --------------------------------

                # Create trace for time measurements
                trace = {
                    "trace_id": uuid.uuid4().hex,
                    "timestamps": {
                        "iot_capture": time.time_ns()
                    }
                }

                event = {
                    "area": area,
                    "trace": trace,
                    "frame_bytes_b64": base64.b64encode(raw).decode()
                }

                await nc.publish(subject, json.dumps(event).encode())

                # Wait for the next frame cycle
                await asyncio.sleep(frame_delay)

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        await nc.drain()


if __name__ == "__main__":
    area = os.environ.get("AREA", "areaA")
    frames_dir = os.environ.get("FRAMES_DIR", "frames")
    fps = float(os.environ.get("FPS", "1"))
    nats_url = os.environ.get("NATS_URL", "nats://98.95.255.36:4222")

    if not os.path.exists(frames_dir):
        print(f"Error: Frames directory '{frames_dir}' not found.")
    else:
        asyncio.run(camera_sender(nats_url, area, frames_dir, fps))