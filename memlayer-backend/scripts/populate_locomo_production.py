"""
LoCoMo Production Population Script - Phase D1.6
Populates production with full LoCoMo dataset.
"""

import asyncio
import httpx
import json
import time
import os
from datetime import datetime, timezone
from pathlib import Path

PRODUCTION_URL = "https://memlayer-prod.onrender.com"
DATASET_PATH = "/Users/overcoder/Code/memlayer/Dataset/locomo10.json"

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJ0ZW5hbnRfaWQiOiJ0ZXN0LXRlbmFudCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc3OTIxOTgzOCwiaWF0IjoxNzc4NjE1MDM4fQ.zPEiUAsoAexJMvWEMCJS_Bw1ukevnjFCAMiFRGfmeow"


def get_auth_headers():
    return {"Authorization": f"Bearer {JWT_TOKEN}", "X-Tenant-ID": "locomo-tenant"}


async def create_workspace(client, name, description=""):
    response = await client.post(
        f"{PRODUCTION_URL}/api/workspaces",
        params={"name": name, "description": description},
        headers=get_auth_headers(),
    )
    return response.json() if response.status_code == 200 else None


async def create_memory(client, workspace_id, raw_content, source_type="conversation"):
    response = await client.post(
        f"{PRODUCTION_URL}/api/workspaces/{workspace_id}/memories",
        json={"raw_content": raw_content, "source_type": source_type},
        headers=get_auth_headers(),
    )
    return response.json() if response.status_code == 200 else None


async def main():
    start_time = time.time()
    metrics = {"conversations": 0, "sessions": 0, "memories": 0, "errors": []}

    print("=" * 60)
    print("LoCoMo Production Population")
    print("=" * 60)

    with open(DATASET_PATH) as f:
        data = json.load(f)

    print(f"Loaded {len(data)} conversations")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Create main workspace
        ws = await create_workspace(
            client, f"locomo-main-{int(time.time())}", "LoCoMo dataset"
        )
        if not ws:
            print("Failed to create workspace")
            return
        ws_id = ws["id"]
        print(f"Created workspace: {ws_id}")

        # Process each conversation
        for conv_idx, conv in enumerate(data):
            metrics["conversations"] += 1
            conv_id = conv.get("sample_id", f"conv-{conv_idx}")

            conv_data = conv.get("conversation", {})

            # Get all sessions
            session_keys = [
                k
                for k in conv_data.keys()
                if k.startswith("session_") and "_date" not in k
            ]
            session_keys.sort(
                key=lambda x: int(x.split("_")[1]) if x.split("_")[1].isdigit() else 0
            )

            for session_key in session_keys:
                metrics["sessions"] += 1
                session_data = conv_data.get(session_key, [])

                if not isinstance(session_data, list):
                    continue

                # Create session summary
                session_num = int(session_key.split("_")[1])
                summary_key = f"session_{session_num}_summary"
                session_summary = conv.get("session_summary", {}).get(summary_key, "")

                if session_summary:
                    await create_memory(
                        client,
                        ws_id,
                        f"Session {session_num}: {session_summary}",
                        "session_summary",
                    )

                # Create message memories
                for msg in session_data:
                    if not isinstance(msg, dict):
                        continue
                    text = msg.get("text", "")
                    speaker = msg.get("speaker", "Unknown")
                    dia_id = msg.get("dia_id", "")

                    if text:
                        content = f"[{dia_id}] {speaker}: {text}"
                        mem = await create_memory(client, ws_id, content, "message")
                        if mem:
                            metrics["memories"] += 1

            if (conv_idx + 1) % 2 == 0:
                print(
                    f"  Processed {conv_idx + 1}/{len(data)} conversations, {metrics['memories']} memories"
                )

        # Final count
        duration = time.time() - start_time
        print(f"\n--- Summary ---")
        print(f"Conversations: {metrics['conversations']}")
        print(f"Sessions: {metrics['sessions']}")
        print(f"Memories: {metrics['memories']}")
        print(f"Duration: {duration:.1f}s")
        print(f"Throughput: {metrics['memories'] / duration:.1f} memories/sec")

    # Save metrics
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration,
        "conversations": metrics["conversations"],
        "sessions": metrics["sessions"],
        "memories": metrics["memories"],
        "workspace_id": ws_id,
    }

    output_path = Path(
        "/Users/overcoder/Code/memlayer/memlayer-backend/docs/runtime_population/LOCOMO_POPULATION_METRICS.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nMetrics saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
