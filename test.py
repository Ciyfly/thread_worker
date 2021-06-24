#!/usr/bin/python
# coding=utf-8
'''
Date: 2021-06-24 18:04:37
LastEditors: recar
LastEditTime: 2021-06-24 18:04:38
'''
from thread_work import LimitWork
import requests
def create_work():
    work = LimitWork(consumer_count=3)
    for i in range(100):
        work.put({"iid": i})
    return work

def consumer(data):
    iid = data["iid"]
    url = "http://127.0.0.1:8088/{0}".format(iid)
    resp = requests.get(url=url).content
    print(resp)

def run():
    work = create_work()
    work.run(consumer)
    print("end")

run()