#!/usr/bin/python
# coding=utf-8
'''
Author: Recar
Date: 2021-06-19 20:10:03
LastEditors: recar
LastEditTime: 2022-02-14 15:38:29
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

def ctrl_c(signum, frame):
    print()
    print("ctrl c")
    sys.exit()
# ctrl+c
signal.signal(signal.SIGINT, ctrl_c)

class BaseWork(object):
    def __init__(self, consumer_func, consumer_count, logger, join, timeout):
        '''
        @params consumer_func consumer_func default None
        @params consumer_count Work quantity
        @params logger You can customize the logger. The default is logging
        @params join You can set whether the thread ends when the queue is empty 
                By default, the thread will end when the queue is empty and the thread task is completed
                You can set it to true to enable work to monitor tasks all the time
        @params timeout The timeout for obtaining data in the queue is 5S by default, that is, if the data is not obtained within 5S, it will end

        '''
        self.consumer_count = consumer_count
        self.work_queue = queue.Queue()
        self.logger = logger
        self.join = join
        self.timeout= timeout
        if consumer_func:
            self.join = True
            self.run(consumer_func)

    def put(self, item):
        '''
        @params item data
        '''        
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put(d)
            else:
                self.work_queue.put(item)
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def producer(self, func):
        pass

    def get_queue_size(self):
        return self.work_queue.qsize()

    def consumer(self, func):
        '''
        @params func consumer func
        '''
        def _consumer(self):
            item = self.work_queue.get(timeout=self.timeout)
            func(item)
        if self.join:
            while True:
                try:
                    _consumer(self)
                except queue.Empty:
                    continue
                except Exception:
                    self.logger.error("consumer error: {0}".format(traceback.format_exc()))
        else:
            while not self.work_queue.empty():
                try:
                    _consumer(self)
                except queue.Empty:
                    return
                except Exception:
                    self.logger.error("consumer error: {0}".format(traceback.format_exc()))                    

    def run(self, consumer_func):
        '''
        @params consumer_func 
        '''
        threads = []
        for _ in range(self.consumer_count):
            t = threading.Thread(target=self.consumer,args=(consumer_func,))
            t.setDaemon(True)
            t.start()
            threads.append(t)
        if not self.join:
            alive = True
            while alive:
                alive_count = len(threads)
                for thread in threads:
                    if not thread.isAlive():
                        alive_count -=1
                if alive_count==0:
                    alive = False
                    self.logger.info("over")
                time.sleep(0.1)

class Worker(BaseWork):
    '''Base Work General consumer queue'''
    def __init__(self, consumer_func=None, consumer_count=10, logger=logging, join=False, timeout=5):
        super(Worker, self).__init__(consumer_func, consumer_count,logger,join, timeout)

class PriorWorker(BaseWork):
    '''Consumption queue with priority'''
    def __init__(self, consumer_func=None, consumer_count=10,logger=logging, join=False, timeout=5):
        super(PriorWorker, self).__init__(consumer_func, consumer_count,logger,join, timeout)
        from queue import PriorityQueue
        self.work_queue = PriorityQueue()
    def put(self, item, priority=1):
        '''
        @params item data
        @params priority default 1
        The smaller the value, the higher the priority
        '''
        try:
            if type(item) == list:
                for d in item:
                    self.work_queue.put((priority, d))
            else:
                self.work_queue.put((priority, item))
        except Exception as e:
            self.logger.error(traceback.format_exc()) 

    def consumer(self, func):
        '''
        @params func 
        '''
        def _consumer(self, func):
            item = self.work_queue.get(timeout=self.timeout)
            priority, data = item
            if data is None:
                return                
            func(data)
        if self.join:
            while True:
                try:
                    _consumer(self, func)
                except queue.Empty:
                    continue
                except Exception:
                    self.logger.error("consumer error: {0}".format(traceback.format_exc()))
        else:
            while not self.work_queue.empty():
                try:
                    _consumer(self, func)
                except queue.Empty:
                    return
                except Exception:
                    self.logger.error("consumer error: {0}".format(traceback.format_exc()))                    


class LimitWorker(BaseWork):
    '''
    queue that can limit flow
    '''
    def __init__(self, limit_time=1, consumer_func=None, consumer_count=10,logger=logging, join=False, timeout=5):
        '''
        @params consumer_count Work quantity
        @params limit_time By setting work_ Count to set work by setting limit_ Time to set the unit time, which controls how many works execute limit together in the unit time_ Time is 1s by default
        '''
        super(LimitWorker, self).__init__(consumer_func, consumer_count,logger,join, timeout)
        self.limit_time = limit_time

    def consumer(self, func):
        '''
        @params func 
        '''
        def _consumer(self, last_time):
            item = self.work_queue.get(timeout=self.timeout)
            while True:
                current_time = datetime.now()
                if last_time is None or (current_time-last_time).seconds >=self.limit_time:
                    func(item)
                    last_time = current_time
                    break
                else:
                    continue
        last_time = None
        if self.join:
            while True:
                try:
                    _consumer(self, last_time)
                except queue.Empty:
                    continue
                except Exception:
                    self.logger.error("consumer error: {0}".format(traceback.format_exc()))
        else:
            while not self.work_queue.empty():
                try:
                    _consumer(self, last_time)
                except queue.Empty:
                    return
                except Exception:
                    self.logger.error("consumer error: {0}".format(traceback.format_exc()))                    
