
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import asyncio
import os
import random
from venv import logger
from app.infrastructure.db.sqlite import init_db 
from app.infrastructure.repositories.process_lock_repository import ProcessLockRepository
from app.infrastructure.repositories.calendar_repository import CalendarRepository
from app.application.sync_calendar_prices_service import SyncCalendarPricesService
from app.infrastructure.booking_experts.booking_experts_client import APIBookingExpertsClient
from app.domain.exceptions.max_batch_errors_exceeded import MaxBatchErrorsExceeded

WORKER_NAME = os.getenv("CALENDAR_WORKER_NAME", "calendar-worker")
IS_SIMPLE = os.getenv("WORKER_IS_SIMPLE", "0") == "1"
BATCH_SIZE = int(os.getenv("WORKER_BATCH_SIZE", "30"))
MAX_BATCHES_PER_TICK = int(os.getenv("WORKER_MAX_BATCHES_PER_TICK", "2"))
INTER_BATCH_SLEEP_MS = int(os.getenv("WORKER_INTER_BATCH_SLEEP_MS", "250"))
IDLE_SLEEP_SEC = int(os.getenv("WORKER_IDLE_SLEEP_SEC", "30"))
LOCK_TTL_SEC = int(os.getenv("WORKER_LOCK_TTL_SEC", "600"))
MAX_ERRORS_PER_TICK = int(os.getenv("WORKER_MAX_ERRORS_PER_TICK", "2"))
MAX_CONSECUTIVE_TICK_FAILURES = int(os.getenv("WORKER_MAX_CONSECUTIVE_TICK_FAILURES", "2"))

async def run_worker():    
    await init_db()
    calendar_repository = CalendarRepository()
    process_lock_repository = ProcessLockRepository()
    booking_experts_client = APIBookingExpertsClient()  # Placeholder, as we don't use it directly in the worker
    service = SyncCalendarPricesService(
        repository=calendar_repository,
        process_lock_repository=process_lock_repository,
        booking_experts_client=booking_experts_client
    )
    acquired = await process_lock_repository.acquire_worker_lock(WORKER_NAME, ttl_seconds=LOCK_TTL_SEC)
    if not acquired:
        logger.info(f"[{WORKER_NAME}] Another worker holds the lock. Exiting.")
        return

    logger.info(f"[{WORKER_NAME}] Started.")    
    consecutive_tick_failures = 0

    try:
        while True:
            # refresh lock so it doesn't expire mid-run
            await process_lock_repository.refresh_worker_lock(WORKER_NAME)

            # Check queue depth
            pending = await calendar_repository.count_unprocessed(is_simple=IS_SIMPLE)
            if pending <= 0:
                # No work: sleep (with a little jitter) and loop
                sleep_s = IDLE_SLEEP_SEC + random.randint(0, 5)
                logger.info(f"[{WORKER_NAME}] No work. Sleeping {sleep_s}s.")
                await asyncio.sleep(sleep_s)
                continue

            logger.info(f"[{WORKER_NAME}] Found {pending} pending rows. Draining...")
            try:
                processed = await service.drain_queue_tick(
                    is_simple=IS_SIMPLE,
                    batch_size=BATCH_SIZE,
                    max_batches_this_tick=MAX_BATCHES_PER_TICK,
                    inter_batch_sleep_ms=INTER_BATCH_SLEEP_MS,
                    max_errors_per_tick=MAX_ERRORS_PER_TICK
                )
                logger.info(f"[{WORKER_NAME}] Processed {processed} row(s) in this tick.")
                consecutive_tick_failures = 0

            except MaxBatchErrorsExceeded as e:
                consecutive_tick_failures += 1
                logger.error(
                    f"[{WORKER_NAME}] Tick failed due to too many errors "
                    f"({consecutive_tick_failures}/{MAX_CONSECUTIVE_TICK_FAILURES}). {e}"
                )
                if consecutive_tick_failures >= MAX_CONSECUTIVE_TICK_FAILURES:
                    logger.error(f"[{WORKER_NAME}] Max consecutive tick failures reached. Stopping worker.")
                    break
                await asyncio.sleep(5.0)  # small backoff between failed ticks

            except Exception as e:
                consecutive_tick_failures += 1
                logger.exception(
                    f"[{WORKER_NAME}] Unexpected error in tick "
                    f"({consecutive_tick_failures}/{MAX_CONSECUTIVE_TICK_FAILURES})."
                )
                if consecutive_tick_failures >= MAX_CONSECUTIVE_TICK_FAILURES:
                    logger.error(f"[{WORKER_NAME}] Max consecutive tick failures reached. Stopping worker.")
                    break
                await asyncio.sleep(5.0)

            # Short pause between ticks to avoid hammering the API
            await asyncio.sleep(1.0 + random.random())

    finally:
        await process_lock_repository.release_worker_lock(WORKER_NAME)
        logger.info(f"[{WORKER_NAME}] Stopped and lock released.")

if __name__ == "__main__":
    asyncio.run(run_worker())
