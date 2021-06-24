#!/usr/bin/python
# coding=utf-8
'''
Author: Recar
Date: 2021-06-19 20:10:03
LastEditors: recar
LastEditTime: 2021-06-24 18:07:46
'''


import sys
import time
try:
    import queue
except:
    import Queue as queue
import signal
import threading
import traceback
import logging
from datetime import datetime

logger = logging
def ctrl_c(signum, frame):
    print()
    print("ctrl c")
    sys.exit()
# ctrl+c
signal.signal(signal.SIGINT, ctrl_c)

class BaseWork(object):
    def __init__(self, consumer_count=50):
        self.consumer_count = consumer_count
        self.work_queue = queue.Queue()

    def put(self, item):
        '''
        @params item 数据
        '''        
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put(d)
            else:
                self.work_queue.put(item)
        except Exception as e:
            logger.error(traceback.format_exc())

    def producer(self, func):
        pass

    def consumer(self, func):
        '''
        消费者
        @params func 消费者函数
        '''
        while not self.work_queue.empty():
            item = self.work_queue.get(timeout=3)
            if item is None:
                break
            func(item)

    def run(self, consumer_func):
        '''
        运行方法
        @params consumer_func 消费者函数
        '''
        logger.info("Starting")
        start_time = time.time()
        threads = []
        for i in range(self.consumer_count):
            t = threading.Thread(target=self.consumer,args=(consumer_func,))
            t.setDaemon(True)
            t.start()
            threads.append(t)
        while not self.work_queue.empty():
            logger.debug("queue size: {0}".format(self.work_queue.qsize()))
            time.sleep(1)
        alive = True
        while alive:
            alive = False
            for thread in threads:
                if thread.isAlive():
                    alive = True
                    time.sleep(0.1)
        use_time = time.time() - start_time
        logger.info("use_time:{0:.2f}s".format(use_time))
        logger.info("End")

class Worker(BaseWork):
    '''普通消费队列'''
    def __init__(self, consumer_count=50):
        super(Worker, self).__init__(consumer_count)
        logger.debug('Worker')

class WorkerPrior(BaseWork):
    '''优先消费队列'''
    def __init__(self, consumer_count=50):
        super(WorkerPrior, self).__init__(consumer_count)
        from queue import PriorityQueue
        self.work_queue = PriorityQueue()
        logger.debug('WorkerPrior')

    def put(self, item, priority=1):
        '''
        @params item 数据
        @params priority 优先级 默认是1
        '''
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put((priority, d))
            else:
                self.work_queue.put((priority, item))
        except Exception as e:
            logger.error(traceback.format_exc()) 

    def consumer(self, func):
        '''
        消费者
        @params func 消费者函数
        '''
        while not self.work_queue.empty():
            item = self.work_queue.get(timeout=3)
            priority, data = item
            if data is None:
                break
            func(data)

class LimitWork(BaseWork):
    '''
    限流work
    '''
    def __init__(self, consumer_count=10):
        super(LimitWork, self).__init__(consumer_count)
        logger.debug('LimitWork')

    def consumer(self, func, limit_time=1):
        '''
        消费者
        @params func 消费者函数
        @params limit_time 限流的每个work的时间限制 默认1s
        '''
        last_time = None
        while not self.work_queue.empty():
            item = self.work_queue.get(timeout=3)
            if item is None:
                break
            while True:
                current_time = datetime.now()
                if last_time is None or (current_time-last_time).seconds >=limit_time:
                    print("send: {0}".format(current_time.strftime('%Y-%m-%d %H:%M:%S %f')))
                    func(item)
                    last_time = current_time
                    break
                else:
                    continue
