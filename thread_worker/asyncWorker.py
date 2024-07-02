#!/usr/bin/python
# coding=utf-8
"""
Author: wanghaisheng
Date: 2024-07-01 20:10:03
LastEditors: wanghaisheng
LastEditTime: 2024-07-01 20:10:03
"""

import sys
import signal
import logging
import asyncio
import traceback
from datetime import datetime
from queue import Empty
from concurrent.futures import ThreadPoolExecutor
import time
from queue import PriorityQueue

def ctrl_c(signum, frame):
    print()
    print("ctrl c")
    sys.exit()

# ctrl+c
signal.signal(signal.SIGINT, ctrl_c)

class AsyncBaseWorker:
    def __init__(self, consumer_func, consumer_count=1, block=True, logger=logging, timeout=3):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.consumer_count = consumer_count
        self.block = block
        self.timeout = timeout if block else None
        self.work_queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        self.run(consumer_func)

    def put(self, item):
        self.loop.create_task(self.work_queue.put(item))

    async def consumer(self, func):
        while True:
            try:
                item = await self.work_queue.get()
                await func(item)
                self.work_queue.task_done()
            except asyncio.QueueEmpty:
                return
            except Exception as e:
                self.logger.error(f"An exception occurred: {e}", exc_info=True)

    def run(self, consumer_func):
        for _ in range(self.consumer_count):
            self.loop.create_task(self.consumer(consumer_func))

    def is_end(self):
        # Check if the queue is empty and all tasks are completed
        return self.work_queue.empty() and not asyncio.all_tasks(self.loop)

class WorkerPrior(AsyncBaseWorker):
    def __init__(self, consumer_func, consumer_count=1, block=True):
        super().__init__(consumer_func, consumer_count, block)
        self.work_queue = PriorityQueue()

    def put(self, item, priority=10):
        self.loop.create_task(self.work_queue.put((priority, item)))

    async def consumer(self, func):
        while True:
            try:
                _, item = await self.work_queue.get()
                await func(item)
                self.work_queue.task_done()
            except asyncio.QueueEmpty:
                return
            except Exception as e:
                self.logger.error(f"An exception occurred: {e}", exc_info=True)
class AsyncLimitWorker(AsyncBaseWorker):
    def __init__(self, consumer_func, consumer_count=1, block=True, limit_time=3):
        super().__init__(consumer_func, consumer_count, block)
        self.limit_time = limit_time
        self.last_process_time = time.time()

    async def consumer(self, func):
        while True:
            try:
                item = await self.work_queue.get()
                current_time = time.time()
                wait_time = max(0, (self.last_process_time + self.limit_time) - current_time)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)  # Enforce rate limit

                await func(item)
                self.last_process_time = time.time()
                self.work_queue.task_done()
            except asyncio.QueueEmpty:
                return
            except Exception as e:
                self.logger.error(f"An exception occurred: {e}", exc_info=True)
