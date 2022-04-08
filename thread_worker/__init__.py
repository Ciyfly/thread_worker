#!/usr/bin/python
# coding=utf-8
'''
Author: Recar
Date: 2021-06-19 20:10:03
LastEditors: recar
LastEditTime: 2022-04-08 10:03:13
'''


import sys
import signal
import logging
import threading
import traceback
from datetime import datetime
from queue import Empty
from queue import PriorityQueue, Queue


def ctrl_c(signum, frame):
    print()
    print("ctrl c")
    sys.exit()
# ctrl+c
signal.signal(signal.SIGINT, ctrl_c)

class BaseWorker(object):
    def __init__(self, consumer_func, consumer_count=1, block=True, logger=logging, timeout=3):
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
        '''
        @params item 数据
        '''
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put(d)
            else:
                self.work_queue.put(item)
        except Exception:
            self.logger.error(traceback.format_exc()) 


    def consumer(self, func):
        '''
        消费者
        @params func 消费者函数
        '''
        while True:
            try:
                item = self.work_queue.get(timeout=self.timeout)
                func(item)
            except Empty:
                return
            except Exception:
                self.logger.error("consumer error: {0}".format(traceback.format_exc()))

    def is_end(self):
        '''
        队列是否空的并且线程永远不会结束那怎么判断任务结束
        '''
        if self.work_queue.qsize() !=0:
            return False
        # 线程是否都结束了
        count = self.consumer_count
        for t in self.threads:
            if not t.isAlive():
                count -=1
        if count ==0:
            return True
        return False

    def run(self, consumer_func):
        '''
        运行方法
        @params consumer_func 消费者函数
        '''
        self.threads = []
        for i in range(self.consumer_count):
            t = threading.Thread(target=self.consumer,args=(consumer_func,))
            t.setDaemon(True)
            t.start()
            self.threads.append(t)

class Worker(BaseWorker):
    '''普通消费队列'''
    def __init__(self, consumer_func, consumer_count=1, block=True):
        super(Worker, self).__init__(consumer_func, consumer_count=consumer_count, block=block)


class WorkerPrior(BaseWorker):
    '''优先消费队列'''
    def __init__(self, consumer_func, consumer_count=1, block=True):
        super(WorkerPrior, self).__init__(consumer_func, consumer_count=consumer_count, block=block)
        self.work_queue = PriorityQueue()

    def put(self, item, priority=10):
        '''
        @params item 数据
        @params priority 优先级 默认是10
        '''
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put((priority, d))
            else:
                self.work_queue.put((priority, item))
        except Exception:
            self.logger.error(traceback.format_exc()) 

    def consumer(self, func):
        '''
        消费者
        @params func 消费者函数
        '''
        while True:
            item = self.work_queue.get()
            try:
                func(item[1])
            except Exception:
                self.logger.error("consumer error: {0}".format(traceback.format_exc()))


class LimitWorker(BaseWorker):
    '''
    限流work
    '''
    def __init__(self, consumer_func, consumer_count=1, block=True, limit_time=1):
        super(LimitWorker, self).__init__(consumer_func, consumer_count=consumer_count, block=block)
        self.limit_time = limit_time

    def consumer(self, func):
        '''
        消费者
        @params func 消费者函数
        '''
        last_time = None
        while not self.work_queue.empty():
            item = self.work_queue.get(timeout=3)
            if item is None:
                break
            while True:
                current_time = datetime.now()
                if last_time is None or (current_time-last_time).seconds >=self.limit_time:
                    print("send: {0}".format(current_time.strftime('%Y-%m-%d %H:%M:%S %f')))
                    func(item)
                    last_time = current_time
                    break
                else:
                    continue