import asyncio
import os

import nats


async def camera_sender(area: str, frames_dir: str, fps: int = 1):
    nc = await nats.connect("nats://nats:4222")
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
                data = f.read()
                await nc.publish(subject, data)
            await asyncio.sleep(frame_delay)


if __name__ == "__main__":
    area = os.environ.get("CAMERA_AREA", "areaA")
    frames_dir = os.environ.get("FRAMES_DIR", "frames")
    fps = int(os.environ.get("FPS", "1"))

    asyncio.run(camera_sender(area, frames_dir, fps))
