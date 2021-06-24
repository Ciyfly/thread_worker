<!--
 * @Date: 2021-06-24 17:51:10
 * @LastEditors: recar
 * @LastEditTime: 2021-06-24 19:17:27
-->
# thread_worker
多线程队列消费work 含有优先级的work 有限流的work

## work
`Worker` 普通多线程work  
`WorkerPrior` 优先消费队列work  
`LimitWork` 限流work  

## 使用

举例 限流的work  
默认一个线程1s发一条 创建三个线程1s发三条  

```python
from thread_worker import LimitWork
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
```
