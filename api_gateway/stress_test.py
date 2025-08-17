import asyncio
import aiohttp
import json
import time

API_URL = "http://localhost:8000/action"
CONCURRENT_REQUESTS = 1000  # Number of simultaneous clients
TOTAL_REQUESTS = 100000      # Total number of requests to send

async def send_action(session, player_id):
    payload = {
        "player_id": player_id,
        "action": "action_4_access_archive"
    }
    async with session.post(API_URL, json=payload) as response:
        status = response.status
        data = await response.text()
        return status, data

async def main():
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(TOTAL_REQUESTS):
            player_id = f"user_{i % 100}"  # simulate 100 different players
            task = asyncio.create_task(send_action(session, player_id))
            tasks.append(task)

            # Control concurrency
            if len(tasks) >= CONCURRENT_REQUESTS:
                results = await asyncio.gather(*tasks)
                tasks = []

        # Await remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks)

    end_time = time.time()
    print(f"Sent {TOTAL_REQUESTS} requests in {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
