#!/usr/bin/python
# coding=utf-8
'''
Date: 2021-06-24 18:04:37
LastEditors: recar
LastEditTime: 2022-04-08 10:15:48
'''
from thread_worker import Worker
import requests
import time
def consumer(iid):
    url = "https://www.baidu.com/{0}".format(iid)
    resp = requests.get(url=url)
    print(resp.request.url)
# block默认就是True的
w = Worker(consumer, consumer_count=1)
for iid in range(10):
    w.put(iid)
# 手动阻塞
while True:
    pass
