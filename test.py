#!/usr/bin/python
# coding=utf-8
'''
Date: 2021-06-24 18:04:37
LastEditors: recar
LastEditTime: 2022-02-14 15:39:05
'''
from thread_worker import Worker
import requests
import time
def consumer(data):
    iid = data["iid"]
    url = "http://127.0.0.1:8088/{0}".format(iid)
    requests.get(url=url).content
def run():
    work = Worker(consumer_func=consumer, consumer_count=1, timeout=None)
    for i in range(100):
            work.put({"iid": i})
    print(work.get_queue_size())
    time.sleep(10)
    print("end")
run()