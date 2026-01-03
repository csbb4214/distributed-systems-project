import asyncio
import os

import nats

#function to simulate the camera stream
async def camera_sender(nats_url: str, area: str, frames_dir: str, fps: int = 1):
    #establish the connection to the NATS-Server
    nc = await nats.connect(nats_url)

    #name of channel on which the images are sent
    subject = f"area.{area}.frame"

    #simulate fps
    frame_delay = 1 / fps

    #list all images and sort alphabetically
    frames = sorted([
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    print(f"Camera from area {area} streaming {len(frames)} frames to {subject}")

    #loop to simulate the stream (repeats endlessly)
    while True:
        for frame_path in frames:
            with open(frame_path, "rb") as f:
                data = f.read()
                await nc.publish(subject, data)
            await asyncio.sleep(frame_delay)


if __name__ == "__main__":
    #configure ENV variables
    area = os.environ.get("AREA", "areaA")
    frames_dir = os.environ.get("FRAMES_DIR", "frames")
    fps = int(os.environ.get("FPS", "1"))
    nats_url = os.environ.get("NATS_URL", "nats://nats:4222")

    asyncio.run(camera_sender(nats_url, area, frames_dir, fps))
