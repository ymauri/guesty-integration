# app/workers/calendar_worker.py
import asyncio
import os
import random
from venv import logger
from app.infrastructure.repositories.process_lock_repository import ProcessLockRepository
from app.application.sync_calendar_prices_service import SyncCalendarPricesService
from domain.booking_experts.services import BookingExpertsClient

WORKER_NAME = os.getenv("CALENDAR_WORKER_NAME", "calendar-worker")
IS_SIMPLE = os.getenv("WORKER_IS_SIMPLE", "0") == "1"
BATCH_SIZE = int(os.getenv("WORKER_BATCH_SIZE", "20"))
MAX_BATCHES_PER_TICK = int(os.getenv("WORKER_MAX_BATCHES_PER_TICK", "5"))
INTER_BATCH_SLEEP_MS = int(os.getenv("WORKER_INTER_BATCH_SLEEP_MS", "250"))
IDLE_SLEEP_SEC = int(os.getenv("WORKER_IDLE_SLEEP_SEC", "30"))
LOCK_TTL_SEC = int(os.getenv("WORKER_LOCK_TTL_SEC", "300"))

async def run_worker():
    repo = ProcessLockRepository()
    service = SyncCalendarPricesService(BookingExpertsClient(), repo)

    acquired = await repo.acquire_worker_lock(WORKER_NAME, ttl_seconds=LOCK_TTL_SEC)
    if not acquired:
        logger.info(f"[{WORKER_NAME}] Another worker holds the lock. Exiting.")
        return

    logger.info(f"[{WORKER_NAME}] Started.")
    try:
        while True:
            # refresh lock so it doesn't expire mid-run
            await repo.refresh_worker_lock(WORKER_NAME)

            # Check queue depth
            pending = await repo.count_unprocessed(is_simple=IS_SIMPLE)
            if pending <= 0:
                # No work: sleep (with a little jitter) and loop
                sleep_s = IDLE_SLEEP_SEC + random.randint(0, 5)
                logger.info(f"[{WORKER_NAME}] No work. Sleeping {sleep_s}s.")
                await asyncio.sleep(sleep_s)
                continue

            logger.info(f"[{WORKER_NAME}] Found {pending} pending rows. Draining...")
            processed = await service.drain_queue_tick(
                is_simple=IS_SIMPLE,
                batch_size=BATCH_SIZE,
                max_batches_this_tick=MAX_BATCHES_PER_TICK,
                inter_batch_sleep_ms=INTER_BATCH_SLEEP_MS
            )
            logger.info(f"[{WORKER_NAME}] Processed {processed} row(s) in this tick.")

            # Short pause between ticks to avoid hammering the API
            await asyncio.sleep(1.0 + random.random())

    finally:
        await repo.release_worker_lock(WORKER_NAME)
        logger.info(f"[{WORKER_NAME}] Stopped and lock released.")

if __name__ == "__main__":
    asyncio.run(run_worker())
