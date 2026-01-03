import asyncio
import nats
import os

#function acts as receiver for alarms
async def alarm_radio(nats_url: str, area: str):
    #establish NATS connection
    nc = await nats.connect(nats_url)

    #name of channel where alarms are received
    subject = f"alerts.{area}"
    print(f"Alarm radio listening on {subject}")

    #message handler
    async def msg_handler(msg):
        text = msg.data.decode()
        print(f"\nALERT for {area}")
        print("Message:", text)
        print("--------------------")

    #listens to channel
    await nc.subscribe(subject, cb=msg_handler)

    #endless loop to permanentely listen to the messages
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    #configure ENV variables
    area = os.environ.get("AREA", "areaA")
    nats_url = os.environ.get("NATS_URL", "nats://nats:4222")

    asyncio.run(alarm_radio(nats_url, area))
