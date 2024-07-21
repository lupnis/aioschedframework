from core import service_task  # 计划任务包装类
from data import *  # 日志
from shared import *  # 共享数据区
...  # 其他的库引用、类定义、变量声明等
# 注意：需要交换的变量等信息请存入data的变量存储区中
raise Exception('DO NOT IMPORT')


@service_task(
    "样例服务",  # 服务名称
    "样例服务的描述",  # 服务描述
    100,  # 服务的执行优先级(默认为-1)
    60,  # 服务最长执行时间 (默认为60秒, 如果为关键任务, 超时将抛出异常)
    False,  # 是否为关键服务 (默认为False)
    'start',  # 服务的触发条件 (默认为start, 表示开始时触发, 如果改为在退出时触发则不会被视作关键服务)
    1, 2, 3,  # run函数传参的*args
    k1=1, k2=2, k3=3  # run函数传参的**kwargs
)
async def run(logger: Logger, *args, **kwargs):
    ...  # 主执行逻辑, 注意不要执行长时间的同步过程，尽量也使用异步库以免阻塞
    # !!!注意!!!
    # 如果使用 try...except， 请对asyncio.exceptions.CancelledError做异常抛出的处理，否则超时后任务将无法退出!!!
