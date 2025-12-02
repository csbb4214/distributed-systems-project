import asyncio
import nats
import os


async def camera_sender(camera_id: str, area: str, frames_dir: str, fps: int = 10):
    nc = await nats.connect("nats://localhost:4222")
    subject = f"camera.{camera_id}.frame"

    frame_delay = 1 / fps
    frames = sorted([
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    print(f"Camera {camera_id} streaming {len(frames)} frames to {subject}")

    while True:
        for frame_path in frames:
            with open(frame_path, "rb") as f:
                data = f.read()
                await nc.publish(subject, data)

            await asyncio.sleep(frame_delay)


# Example:
# asyncio.run(camera_sender("cam01", "areaA", "frames_cam01"))
asyncio.run(
    camera_sender(
        camera_id="cam01",
        area="areaA",
        frames_dir="frames_cam01",
        fps=10
    )
)
