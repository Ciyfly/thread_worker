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
    def __init__(self, consumer_func, consumer_count, logger, block, timeout):
        '''
        @params consumer_func consumer_func default None
        @params consumer_count Work quantity
        @params logger You can customize the logger. The default is logging
        @params block You can set whether the thread ends when the queue is empty 
                By default, the thread will end when the queue is empty and the thread task is completed
                You can set it to true to enable work to monitor tasks all the time
        @params timeout The timeout for obtaining data in the queue is 5S by default, that is, if the data is not obtained within 5S, it will end

        '''
```
consumer_func 消费者函数 默认为None 如果加上了 就认为是先启动消费者再生成任务
consumer_count 是控制有多少个消费者  
logger 是设置日志输出  
block 是控制是否是阻塞模式 如果设置为True 那么work线程会一直执行 直到主进程结束 否则 当队列为空且线程任务都完成就将work结束  
timeout 是从队列获取数据的超时时间 默认是5s 超过5s 如果join是True则work重新再取 join为False则结束当前work  

## 生产者消费者模式有两种使用场景
一种是先把消费者跑起来然后再生成
可以持续生成持续消费 适合被动代理扫描任务或者说一个主进程控制全局然后生成任务  

一种是一次性把任务都生成好交给消费者跑  
适合一次性就生成测试的任务 然后跑就完事了  


## 通过work.is_end 方法来阻塞多线程任务

1. 定义消费者函数
2. 实例一个`Work`
3. 通过实例的`Work` `put`数据给消费者函数
4. 通过 `Work.is_end()`方法阻塞程序

### 基础版worker
```python
from thread_worker import Worker
import requests
import time
def consumer(iid):
    url = "https://www.baidu.com/{0}".format(iid)
    resp = requests.get(url=url)
    print(resp.request.url)
# 不需要阻塞
w = Worker(consumer, consumer_count=1, block=False)
for iid in range(10):
    w.put(iid)
# 这里通过 is_end 方法来阻塞程序 
while not w.is_end():
    time.sleep(3)
```

### 创建一个限流的work  
与默认的Work一样 只是在创建的时候多了一个 `limit_time` 参数  
通过设置 单位时间 `limit_time` 和 `consumer_count` 来控制单位时间内执行多少个work  
默认 `limit_time` 是1s

```python
from thread_worker import LimitWorker
import requests
import time
def consumer(iid):
    url = "https://www.baidu.com/{0}".format(iid)
    resp = requests.get(url=url)
    print(resp.request.url)
# limit_time 是limit_time 秒内有 consumer_count个消费者
w = LimitWorker(consumer, consumer_count=1, block=False, limit_time=3)
for iid in range(10):
    w.put(iid)
# 这里通过 is_end 方法来阻塞程序 
while not w.is_end():
    time.sleep(3)
```

输出是这样的 每3s才会发一个请求即控制频率
```
send: 2022-04-08 10:13:04 904000
https://www.baidu.com/0
send: 2022-04-08 10:13:07 904000
https://www.baidu.com/1
send: 2022-04-08 10:13:10 904000
https://www.baidu.com/2
send: 2022-04-08 10:13:13 904000
https://www.baidu.com/3
send: 2022-04-08 10:13:16 904000
https://www.baidu.com/4
send: 2022-04-08 10:13:19 904000
https://www.baidu.com/5
send: 2022-04-08 10:13:22 904000
https://www.baidu.com/6
send: 2022-04-08 10:13:25 904000
https://www.baidu.com/7
send: 2022-04-08 10:13:28 904000
https://www.baidu.com/8
send: 2022-04-08 10:13:31 904000
https://www.baidu.com/9
```
## 先把消费者运行起来监听队列再不断生成任务  

这里的场景时候被动代理或者一些主进程会长期运行的程序中使用  
与上面不同的是 不需要 Work.is_end()方法阻塞 block也不需要设置 block默认则是True的 

```python
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

```


