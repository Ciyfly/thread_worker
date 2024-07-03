# Example usage
import logging
import asyncio
import sys
from thread_worker import AsyncLimitWorker

logger = logging.getLogger('AsyncWorkerLogger')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
async def example_consumer(item):
    logger.info(f"Starting processing for item: {item}")
    # Simulate some work with an asynchronous sleep
    await asyncio.sleep(1)
    logger.info(f"Finished processing for item: {item}")

async def demo_client():
    # Create an instance of the worker with the example_consumer function
    worker = AsyncLimitWorker(example_consumer, consumer_count=1, block=False, limit_time=3)

    # List of items to process
    items_to_process = [f"item-{i}" for i in range(1, 6)]

    # Put items into the worker's queue
    for item in items_to_process:
        await worker.put(item)

    # Wait for all items to be processed
    await worker.work_queue.join()

    # Check if all tasks are completed
    if worker.is_end():
        logger.info("All tasks completed")

# Entry point for the demo client
if __name__ == "__main__":
    # Run the demo_client coroutine。
    asyncio.run(demo_client())