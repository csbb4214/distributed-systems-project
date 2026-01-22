import asyncio
import os
import time
import uuid
import json
import base64
import nats
import cv2
import numpy as np

NATS_URL = "nats://98.95.255.36:4222"

# SERVICE 1: CAMERA SENDER (Produces Frames)
async def service_camera(area: str, frames_dir: str, fps: float):
    try:
        nc = await nats.connect(NATS_URL)
        print(f"[Camera {area}] Connected to NATS")
    except Exception as e:
        print(f"[Camera {area}] Connection failed: {e}")
        return

    subject = f"area.{area}.frame"
    frame_delay = 1 / fps

    if not os.path.exists(frames_dir):
        print(f"[Camera {area}] ERROR: Directory '{frames_dir}' not found.")
        return

    frames = sorted([
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    if not frames:
        print(f"[Camera {area}] No images found in {frames_dir}")
        return

    print(f"[Camera {area}] Streaming {len(frames)} frames to subject '{subject}'")

    window_name = f"Cam: {area}"

    try:
        while True:
            for frame_path in frames:
                # 1. Read Image
                with open(frame_path, "rb") as f:
                    raw = f.read()

                # 2. Local Visualization (OpenCV)
                nparr = np.frombuffer(raw, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # Add text overlay for visual confirmation
                cv2.putText(img, f"Area: {area}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow(window_name, img)

                # Required for OpenCV to update window.
                # Check for 'q' to quit locally.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Quit signal received.")
                    return

                # 3. Publish to NATS
                trace = {
                    "trace_id": uuid.uuid4().hex,
                    "timestamps": {"iot_capture": time.time_ns()}
                }

                event = {
                    "area": area,
                    "trace": trace,
                    "frame_bytes_b64": base64.b64encode(raw).decode()
                }

                await nc.publish(subject, json.dumps(event).encode())

                # 4. Sleep to match FPS
                await asyncio.sleep(frame_delay)

    except asyncio.CancelledError:
        print(f"[Camera {area}] Stopping...")
    finally:
        await nc.drain()
        # We don't destroy windows here to avoid flickering if one service stops early,
        # we will close all at the end of main.


# SERVICE 2: ALARM LISTENER (Consumes/Traces)
TRACE_LOG = "/traces.jsonl"
async def service_alarm(area: str):
    nc = await nats.connect(NATS_URL)

    subject = f"alerts.{area}"
    print(f"Alarm radio listening on {subject}")

    async def msg_handler(msg):
        payload = json.loads(msg.data.decode())

        text = payload["text"]
        trace = payload["trace"]

        # Close the trace
        trace["timestamps"]["iot_alarm_received"] = time.time_ns()

        print(f"\nALERT for {area}")
        print("Message:", text)
        print("Trace ID:", trace["trace_id"])
        print("--------------------")

        # Persist trace for later analysis
        with open(TRACE_LOG, "a") as f:
            f.write(json.dumps(trace) + "\n")

    await nc.subscribe(subject, cb=msg_handler)

    while True:
        await asyncio.sleep(1)


async def main():
    print("--- Starting Local Simulation (Press Ctrl+C to stop) ---")

    tasks = [
        # Camera Area 01
        asyncio.create_task(service_camera(
            area="area01",
            frames_dir="./frames_cam01",  # Pointing to local folder
            fps=0.5
        )),

        # Camera Area 02 (Uses same frames folder as per your compose file)
        asyncio.create_task(service_camera(
            area="area02",
            frames_dir="./frames_cam01",
            fps=0.5
        )),

        # Alarm Area 01
        asyncio.create_task(service_alarm(area="area01")),

        # Alarm Area 02
        asyncio.create_task(service_alarm(area="area02")),
    ]

    try:
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n--- Stopping Simulation ---")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Ensure event loop handles Ctrl+C cleanly
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass