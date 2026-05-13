"""
Quick LoCoMo Population Test - Phase D1.6
Validates that memory creation works with real conversation data.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime, timezone

PRODUCTION_URL = "https://memlayer-prod.onrender.com"
DATASET_PATH = "/Users/overcoder/Code/memlayer/Dataset/locomo10.json"

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJ0ZW5hbnRfaWQiOiJ0ZXN0LXRlbmFudCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc3OTIxOTgzOCwiaWF0IjoxNzc4NjE1MDM4fQ.zPEiUAsoAexJMvWEMCJS_Bw1ukevnjFCAMiFRGfmeow"


def get_auth_headers():
    return {"Authorization": f"Bearer {JWT_TOKEN}", "X-Tenant-ID": "test-tenant"}


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
    print("=" * 60)
    print("LoCoMo Quick Population Test")
    print("=" * 60)

    with open(DATASET_PATH) as f:
        data = json.load(f)

    print(f"Loaded {len(data)} conversations")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Create workspace
        ws = await create_workspace(
            client, f"locomo-test-{int(time.time())}", "LoCoMo test"
        )
        if not ws:
            print("Failed to create workspace")
            return
        print(f"Created workspace: {ws['id']}")

        # Create just 20 memories from first conversation
        conv = data[0]
        conv_data = conv.get("conversation", {})

        session_1 = conv_data.get("session_1", [])
        memories_created = 0

        for i, msg in enumerate(session_1[:20]):
            text = msg.get("text", "")
            speaker = msg.get("speaker", "Unknown")
            if text:
                mem = await create_memory(client, ws["id"], f"[{speaker}] {text}")
                if mem:
                    memories_created += 1
                    if memories_created % 5 == 0:
                        print(f"  Created {memories_created} memories...")

        print(f"\nTotal memories created: {memories_created}")

        # Try retrieval
        response = await client.get(
            f"{PRODUCTION_URL}/api/workspaces/{ws['id']}/memories",
            headers=get_auth_headers(),
        )
        if response.status_code == 200:
            memories = response.json()
            print(f"Verified {len(memories)} memories in workspace")

        # Test semantic search (if available)
        try:
            response = await client.get(
                f"{PRODUCTION_URL}/api/workspaces/{ws['id']}/memories/search",
                params={"query": "support group", "top_k": 3},
                headers=get_auth_headers(),
            )
            if response.status_code == 200:
                results = response.json()
                print(f"Search test: found {len(results)} results")
        except Exception as e:
            print(f"Search test: {e}")

    print("\n" + "=" * 60)
    print("Population test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
