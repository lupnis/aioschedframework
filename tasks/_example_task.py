from core import scheduled_task  # 计划任务包装类
from data import *  # 日志
from shared import *  # 共享数据区
...  # 其他的库引用、类定义、变量声明等
# 注意：需要交换的变量等信息请存入data的变量存储区中
raise Exception('DO NOT IMPORT')


@scheduled_task(
    "样例任务",  # 任务名称
    "样例任务的描述",  # 任务描述
    "* * * * *",  # 定时CRON表达式 (默认为 * * * * *)
    False,  # 是否只触发一次 (默认为False)
    60,  # 执行最长时间 (默认为60秒)
    False, # 是否在创建任务后立刻执行 (默认为False)
    1, 2, 3,  # run函数传参的*args (可选)
    k1=1, k2=2, k3=3  # run函数传参的**kwargs (可选)
)
async def run(logger: Logger, *args, **kwargs):
    ...  # 主执行逻辑, 注意不要执行长时间的同步过程，尽量也使用异步库以免阻塞
    # !!!注意!!!
    # 如果使用 try...except， 请对asyncio.exceptions.CancelledError做异常抛出的处理，否则超时后任务将无法退出!!!
    return 0  # 返回值为0的情况下周期性任务才能周期执行
