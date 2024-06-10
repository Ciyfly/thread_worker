from thread_worker import LimitWorker, Worker
import requests
import time


def consumer(data):
    url = "https://www.baidu.com/{0}".format(data["data"])
    resp = requests.get(url=url)
    print(resp.request.url)


# limit_time 是limit_time 秒内有 consumer_count个消费者
w = LimitWorker(consumer, consumer_count=1, block=False, limit_time=3)
# w = Worker(consumer, consumer_count=1, block=False)

for iid in range(10):
    w.put({"data": iid, "index": 0})
# 这里通过 is_end 方法来阻塞程序
while not w.is_end():
    time.sleep(3)

# pip install thread_worker
