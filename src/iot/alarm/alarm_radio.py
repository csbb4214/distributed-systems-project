import asyncio
import nats
import os
import json
import time


TRACE_LOG = "traces.jsonl"   # newline-delimited JSON for easy plotting

# function acts as receiver for alarms
async def alarm_radio(nats_url: str, area: str):
    nc = await nats.connect(nats_url)

    subject = f"alerts.{area}"
    print(f"Alarm radio listening on {subject}")

    async def msg_handler(msg):
        payload = json.loads(msg.data.decode())

        text = payload["text"]
        trace = payload["trace"]

        # Close the trace
        trace["timestamps"]["iot_alarm_received"] = time.monotonic_ns()

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


if __name__ == "__main__":
    area = os.environ.get("AREA", "areaA")
    nats_url = os.environ.get("NATS_URL", "nats://98.95.255.36:4222")

    asyncio.run(alarm_radio(nats_url, area))
