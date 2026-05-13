"""
Fast LoCoMo Population - Phase D1.6
Batched memory creation for speed.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime, timezone

PRODUCTION_URL = "https://memlayer-prod.onrender.com"
DATASET_PATH = "/Users/overcoder/Code/memlayer/Dataset/locomo10.json"

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJ0ZW5hbnRfaWQiOiJ0ZXN0LXRlbmFudCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc3OTIxOTgzOCwiaWF0IjoxNzc4NjE1MDM4fQ.zPEiUAsoAexJMvWEMCJS_Bw1ukevnjFCAMiFRGfmeow"


async def main():
    start = time.time()

    with open(DATASET_PATH) as f:
        data = json.load(f)

    print(f"Loaded {len(data)} conversations")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Create workspace
        r = await client.post(
            f"{PRODUCTION_URL}/api/workspaces",
            params={"name": f"locomo-{int(time.time())}", "description": "LoCoMo full"},
            headers={
                "Authorization": f"Bearer {JWT_TOKEN}",
                "X-Tenant-ID": "test-tenant",
            },
        )
        ws = r.json()
        ws_id = ws["id"]
        print(f"Workspace: {ws_id}")

        # Gather all messages
        all_messages = []
        for conv in data:
            conv_data = conv.get("conversation", {})
            for key in conv_data:
                if key.startswith("session_") and "_date" not in key:
                    session = conv_data[key]
                    if isinstance(session, list):
                        for msg in session:
                            if isinstance(msg, dict) and msg.get("text"):
                                text = msg.get("text", "")
                                speaker = msg.get("speaker", "Unknown")
                                dia_id = msg.get("dia_id", "")
                                if text:
                                    all_messages.append(f"[{dia_id}] {speaker}: {text}")

        print(f"Total messages to ingest: {len(all_messages)}")

        # Batch create with limited concurrency
        batch_size = 10
        total_created = 0

        for i in range(0, len(all_messages), batch_size):
            batch = all_messages[i : i + batch_size]
            tasks = [
                client.post(
                    f"{PRODUCTION_URL}/api/workspaces/{ws_id}/memories",
                    json={"raw_content": msg, "source_type": "message"},
                    headers={
                        "Authorization": f"Bearer {JWT_TOKEN}",
                        "X-Tenant-ID": "test-tenant",
                    },
                )
                for msg in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(
                1
                for r in results
                if not isinstance(r, Exception) and r.status_code == 200
            )
            total_created += successful

            if (i // batch_size + 1) % 5 == 0:
                print(f"  Progress: {total_created}/{len(all_messages)}")

        duration = time.time() - start
        print(f"\nDone! Created {total_created} memories in {duration:.1f}s")

        # Verify
        r = await client.get(
            f"{PRODUCTION_URL}/api/workspaces/{ws_id}/memories",
            headers={
                "Authorization": f"Bearer {JWT_TOKEN}",
                "X-Tenant-ID": "test-tenant",
            },
        )
        mems = r.json()
        print(f"Verified: {len(mems)} memories in workspace")


asyncio.run(main())
