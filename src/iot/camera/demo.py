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

# --- NEW: Display Constants ---
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
WINDOW_MARGIN = 50

# SERVICE 1: CAMERA SENDER (Produces Frames)
async def service_camera(area: str, frames_dir: str, fps: float, window_x: int, window_y: int):
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

    # --- NEW: Setup Window Position ---
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, DISPLAY_WIDTH, DISPLAY_HEIGHT)
    cv2.moveWindow(window_name, window_x, window_y)

    try:
        while True:
            for frame_path in frames:
                # 1. Read Image
                with open(frame_path, "rb") as f:
                    raw = f.read()

                # 2. Local Visualization (OpenCV)
                nparr = np.frombuffer(raw, np.uint8)
                original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # --- NEW: Resize for display ---
                display_img = cv2.resize(original_img, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

                # Add text overlay
                cv2.putText(display_img, f"Area: {area}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow(window_name, display_img)

                # Required for OpenCV to update window.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Quit signal received.")
                    return

                # 3. Publish to NATS (Send ORIGINAL raw bytes, not resized)
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


# SERVICE 2: ALARM LISTENER (Consumes/Traces)
TRACE_LOG = "traces.jsonl" # Cleaned up path for local run
async def service_alarm(area: str):
    try:
        nc = await nats.connect(NATS_URL)
    except Exception as e:
        print(f"[Alarm {area}] Connection failed: {e}")
        return

    subject = f"alerts.{area}"
    print(f"Alarm radio listening on {subject}")

    async def msg_handler(msg):
        payload = json.loads(msg.data.decode())

        text = payload.get("text", "Alert")
        trace = payload.get("trace", {})

        if "timestamps" in trace:
             trace["timestamps"]["iot_alarm_received"] = time.time_ns()

        print(f"\nALERT for {area}")
        print("Message:", text)
        print("Trace ID:", trace.get("trace_id", "N/A"))
        print("--------------------")

        # Persist trace for later analysis
        with open(TRACE_LOG, "a") as f:
            f.write(json.dumps(trace) + "\n")

    await nc.subscribe(subject, cb=msg_handler)

    while True:
        await asyncio.sleep(1)


async def main():
    print("--- Starting Local Simulation (Press Ctrl+C to stop) ---")

    # --- NEW: Calculate Coordinates ---
    # Window 1: Top Left
    cam1_x = WINDOW_MARGIN
    cam1_y = WINDOW_MARGIN

    # Window 2: Right of Window 1
    cam2_x = WINDOW_MARGIN + DISPLAY_WIDTH + WINDOW_MARGIN
    cam2_y = WINDOW_MARGIN

    tasks = [
        # Camera Area 01
        asyncio.create_task(service_camera(
            area="area01",
            frames_dir="./frames_cam01",
            fps=0.5,
            window_x=cam1_x, # Pass coordinates
            window_y=cam1_y
        )),

        # Camera Area 02
        asyncio.create_task(service_camera(
            area="area02",
            frames_dir="./frames_cam02",
            fps=0.5,
            window_x=cam2_x, # Pass coordinates
            window_y=cam2_y
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass