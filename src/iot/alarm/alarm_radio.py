import asyncio
import nats
import os

async def alarm_radio(nats_url: str, area: str):
    nc = await nats.connect(nats_url)

    subject = f"alerts.{area}"
    print(f"Alarm radio listening on {subject}")

    async def msg_handler(msg):
        text = msg.data.decode()
        print(f"\nALERT for {area}")
        print("Message:", text)
        print("--------------------")

    await nc.subscribe(subject, cb=msg_handler)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    area = os.environ.get("AREA", "areaA")
    nats_url = os.environ.get("NATS_URL", "nats://nats:4222")

    asyncio.run(alarm_radio(nats_url, area))
