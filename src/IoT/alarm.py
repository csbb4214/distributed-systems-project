import asyncio
import nats

async def alarm_radio(area: str):
    nc = await nats.connect("nats://localhost:4222")

    subject = f"alerts.{area}"
    print(f"Alarm device listening to: {subject}")

    async def msg_handler(msg):
        text = msg.data.decode()
        print(f"\n🚨 ALERT for {area} 🚨")
        print("Message:", text)
        print("-------------------------")

    await nc.subscribe(subject, cb=msg_handler)

    while True:
        await asyncio.sleep(1)

asyncio.run(alarm_radio("areaA"))
