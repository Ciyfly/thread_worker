#!/usr/bin/python
# coding=utf-8
"""
Author: Recar
Date: 2021-06-19 20:10:03
LastEditors: recar
LastEditTime: 2022-04-08 10:03:13
"""


import sys
import signal
import logging
import threading
import traceback
from datetime import datetime
from queue import Empty
from queue import PriorityQueue, Queue
from threading import Lock
import time
import asyncio


def ctrl_c(signum, frame):
    print()
    print("ctrl c")
    sys.exit()


# ctrl+c
signal.signal(signal.SIGINT, ctrl_c)


class BaseWorker(object):
    def __init__(
        self, consumer_func, consumer_count=1, block=True, logger=logging, timeout=3
    ):
        self.logger = logger
        self.consumer_count = consumer_count
        self.block = block
        if self.block:
            self.timeout = None
        else:
            self.timeout = timeout
        self.work_queue = Queue()
        self.run(consumer_func)

    def put(self, item):
        """
        @params item 数据
        """
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put(d)
            else:
                self.work_queue.put(item)
        except Exception:
            self.logger.error(traceback.format_exc())

    def consumer(self, func):
        """
        消费者
        @params func 消费者函数
        """
        while True:
            try:
                item = self.work_queue.get(timeout=self.timeout)
                func(item)
            except Empty:
                return
            except Exception:
                self.logger.error("consumer error: {0}".format(traceback.format_exc()))

    def is_end(self):
        """
        队列是否空的并且线程永远不会结束那怎么判断任务结束
        """
        if self.work_queue.qsize() != 0:
            return False
        # 线程是否都结束了
        count = self.consumer_count
        for t in self.threads:
            if not t.is_alive():
                count -= 1
        if count == 0:
            return True
        return False

    def run(self, consumer_func):
        """
        运行方法
        @params consumer_func 消费者函数
        """
        self.threads = []
        for i in range(self.consumer_count):
            t = threading.Thread(target=self.consumer, args=(consumer_func,))
            t.setDaemon(True)
            t.start()
            self.threads.append(t)


class Worker(BaseWorker):
    """普通消费队列"""

    def __init__(self, consumer_func, consumer_count=1, block=True):
        super(Worker, self).__init__(
            consumer_func, consumer_count=consumer_count, block=block
        )


class WorkerPrior(BaseWorker):
    """优先消费队列"""

    def __init__(self, consumer_func, consumer_count=1, block=True):
        super(WorkerPrior, self).__init__(
            consumer_func, consumer_count=consumer_count, block=block
        )
        self.work_queue = PriorityQueue()

    def put(self, item, priority=10):
        """
        @params item 数据
        @params priority 优先级 默认是10
        """
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put((priority, d))
            else:
                self.work_queue.put((priority, item))
        except Exception:
            self.logger.error(traceback.format_exc())

    def consumer(self, func):
        """
        消费者
        @params func 消费者函数
        """
        while True:
            item = self.work_queue.get()
            try:
                func(item[1])
            except Exception:
                self.logger.error("consumer error: {0}".format(traceback.format_exc()))


class LimitWorker(BaseWorker):
    def __init__(self, consumer_func, consumer_count=1, block=True, limit_time=3):
        super().__init__(consumer_func, consumer_count, block)
        self.limit_time = limit_time
        self.last_process_time = time.time()
        self.lock = Lock()

    def consumer(self, func):
        while True:
            try:
                item = self.work_queue.get(timeout=self.timeout)
                if item is None:
                    break

                # Calculate wait time
                with self.lock:
                    current_time = time.time()
                    wait_time = max(
                        0, (self.last_process_time + self.limit_time) - current_time
                    )
                    if wait_time > 0:
                        time.sleep(wait_time)  # Sleep if needed to enforce rate limit

                # Execute the consumer function
                func(item)

                # Update last process time
                with self.lock:
                    self.last_process_time = time.time()

            except Empty:
                break
            except Exception as e:
                self.logger.error(
                    "An exception occurred in consumer: %s", e, exc_info=True
                )
                break

    # Override the is_end method to wait for threads to finish processing
    def is_end(self):
        with self.lock:
            if not self.work_queue.qsize():
                return not any(t.is_alive() for t in self.threads)
        return False

class AsyncBaseWorker:
    def __init__(self, consumer_func, consumer_count=1, block=True, logger=logging, timeout=3):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.consumer_count = consumer_count
        self.block = block
        self.timeout = timeout if block else None
        self.work_queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
        self.run(consumer_func)

    async def put(self, item):
        await self.work_queue.put(item)

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
        # return self.work_queue.empty() and not asyncio.all_tasks(self.loop)
        return self.work_queue.empty() and not self.loop.is_running()

class AsyncWorkerPrior(AsyncBaseWorker):
    def __init__(self, consumer_func, consumer_count=1, block=True):
        super(AsyncWorkerPrior,self).__init__(consumer_func, consumer_count, block)
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
