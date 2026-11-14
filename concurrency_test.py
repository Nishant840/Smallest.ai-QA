
import asyncio
import json
import os
import time
from datetime import datetime, timezone

import websockets
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SMALLEST_API_KEY")
URL = "wss://api.smallest.ai/waves/v1/tts/live"
TIMEOUT = 90

if not API_KEY:
    raise RuntimeError("SMALLEST_API_KEY not found in .env")

headers = {"Authorization": f"Bearer {API_KEY}"}

first_signal = asyncio.Event()
first_signal_status = None
events = {"request_a": [], "request_b": []}


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def make_request(text):
    return {
        "text": text,
        "voice_id": "meher",
        "model": "lightning_v3.1_pro",
        "output_format": "wav"
    }


async def receive_responses(ws, label):
    global first_signal_status

    started = time.monotonic()
    print(f"\n[{label}] Listening for responses...")

    while time.monotonic() - started < TIMEOUT:
        try:
            remaining = TIMEOUT - (time.monotonic() - started)
            raw = await asyncio.wait_for(ws.recv(), timeout=remaining)

            received_at = timestamp()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[{label}] Received non-JSON message")
                continue

            status = message.get("status")

            # Do not save Base64 audio data.
            event = {
                "timestamp": received_at,
                "status": status,
                "request_id": message.get("request_id"),
                "session_id": message.get("session_id"),
                "message": message.get("message"),
            }

            events[label].append(event)

            print(
                f"[{label}] {received_at} | "
                f"status={status} | "
                f"request_id={message.get('request_id')}"
            )

            if status == "chunk":
                if label == "request_a" and not first_signal.is_set():
                    first_signal_status = "chunk"
                    first_signal.set()

            elif status in ("complete", "error"):
                if label == "request_a" and not first_signal.is_set():
                    first_signal_status = status
                    first_signal.set()

                if status == "error":
                    print(f"[{label}] Error: {message}")

                return

        except asyncio.TimeoutError:
            print(f"[{label}] Timed out waiting for response")
            events[label].append({
                "timestamp": timestamp(),
                "status": "client_timeout"
            })
            return

        except websockets.ConnectionClosed as exc:
            print(f"[{label}] Connection closed: {exc}")
            events[label].append({
                "timestamp": timestamp(),
                "status": "connection_closed",
                "message": str(exc)
            })
            return


async def run_test():
    global first_signal_status

    text_a = (
        "This is the first request for a controlled concurrency test. "
        * 35
    )

    text_b = (
        "This is the second request sent while the first request "
        "is actively generating audio."
    )

    print("Connecting two WebSocket clients...")

    async with (
        websockets.connect(URL, additional_headers=headers) as ws_a,
        websockets.connect(URL, additional_headers=headers) as ws_b
    ):
        print("Both WebSocket connections established.")

        # Send request A first.
        print("\nSending request A...")
        await ws_a.send(json.dumps(make_request(text_a)))

        receiver_a = asyncio.create_task(
            receive_responses(ws_a, "request_a")
        )

        # Wait until A starts returning audio.
        try:
            await asyncio.wait_for(first_signal.wait(), timeout=20)
        except asyncio.TimeoutError:
            print("Request A produced no response within 20 seconds.")
            receiver_a.cancel()
            return

        print(
            f"\nRequest A signal received: {first_signal_status}"
        )

        if first_signal_status != "chunk":
            print("A did not produce an audio chunk. "
                  "Skipping request B to avoid a misleading test.")
            await receiver_a
            return

        # Send request B immediately after A's first audio chunk.
        print("\nSending request B on the second connection...")
        await ws_b.send(json.dumps(make_request(text_b)))

        receiver_b = asyncio.create_task(
            receive_responses(ws_b, "request_b")
        )

        await asyncio.gather(receiver_a, receiver_b)

    with open("concurrency_results.json", "w") as file:
        json.dump(events, file, indent=2)

    print("\nTest finished.")
    print("Results saved to concurrency_results.json")


if __name__ == "__main__":
    asyncio.run(run_test())
