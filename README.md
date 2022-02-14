# thread_worker
方便的使用生产者消费者模式 使用多线程+队列  
支持 正常的一个生产者多个消费者模式  
支持 优先消费队列模式  
支持 限流work模式  


## work
`Worker` 普通多线程work  
`PriorWorker` 优先消费队列work  
`LimitWorker` 限流work  

## 使用
初始化的话有如下参数  
```python
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
```
consumer_func 消费者函数 默认为None 如果加上了 就认为是先启动消费者再生成任务
consumer_count 是控制有多少个消费者  
logger 是设置日志输出  
join 是控制是否是阻塞模式 如果设置为True 那么work线程会一直执行 直到主进程结束 否则 当队列为空且线程任务都完成就将work结束  
timeout 是从队列获取数据的超时时间 默认是5s 超过5s 如果join是True则work重新再取 join为False则结束当前work  

## 生产者消费者模式有两种使用场景
一种是先把消费者跑起来然后再生成
可以持续生成持续消费 适合被动代理扫描任务或者说一个主进程控制全局然后生成任务  

一种是一次性把任务都生成好交给消费者跑  
适合一次性就生成测试的任务 然后跑就完事了  


## 先生成任务后消费

先创建work 然后通过work put任务 最后run 消费者函数

### 基础版worker
```python
from thread_worker import Worker
import requests
def create_work():
    work = Worker(consumer_count=1)
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

### 创建一个限流的work  
通过设置 单位时间 `limit_time` 和 `consumer_count` 来控制单位时间内执行多少个work  
默认 `limit_time` 是1s
```python
from thread_worker import LimitWorker
import requests
def create_work():
    work = LimitWorker(consumer_count=3)
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

## 先把消费者运行起来监听队列再不断生成任务  

这里需要注释的是 需要一个全局进程去控制 否则work会因为没有被阻塞被挂掉  

```python
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
```


