import asyncio
import nats
import os

async def alarm_radio(area: str):
    nc = await nats.connect("nats://nats:4222")

    subject = f"alerts.{area}"
    print(f"Alarm radio listening on {subject}")

    async def msg_handler(msg):
        text = msg.data.decode()
        print(f"\n🚨 ALERT for {area} 🚨")
        print("Message:", text)
        print("--------------------")

    await nc.subscribe(subject, cb=msg_handler)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    area = os.environ.get("AREA", "areaA")
    asyncio.run(alarm_radio(area))
