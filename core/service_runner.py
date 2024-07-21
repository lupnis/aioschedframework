import asyncio
from asyncio.exceptions import CancelledError

from data import Logger
from data.logs import Styled, Styles

import gc

import traceback


class ServiceTask:
    def __init__(self, name="undefined",
                 descriptions="undefined",
                 start_priority=-1,
                 max_running_time=60,
                 critical=False,
                 trigger='start',
                 func=None,
                 *args,
                 **kwargs):
        self.name = name
        self.descriptions = descriptions
        self.start_priority = start_priority
        self.max_running_time = max_running_time
        self.critical = critical if trigger == 'start' else False
        self.trigger = trigger
        self.func = func
        self.running_args = args
        self.running_kwargs = kwargs

    async def run(self, logger):
        if self.func:
            await logger.info('==============================执行系统服务==============================')
            await logger.info(' * 服务名称: {}', Styled(self.name, Styles.CYAN))
            await logger.info(' * 服务描述: {}', Styled(self.descriptions, Styles.CYAN))
            await logger.info(' * 关键服务: {}', Styled('是', Styles.GREEN) if self.critical else Styled('否', Styles.BRIGHT_BLACK))
            await logger.info(' * 优先等级: {}', Styled(self.start_priority, Styles.CYAN))
            await logger.info(' * 触发方式: {}', Styled('启动时触发', Styles.CYAN) if self.trigger == 'start' else Styled('退出时触发', Styles.CYAN_BG, Styles.BLACK))
            await logger.info(' * 超时时长: {}', Styled(self.max_running_time, Styles.CYAN))
            try:
                await asyncio.wait_for(self.func(*self.running_args, **self.running_kwargs, logger=logger), self.max_running_time)
                gc.collect()
                await logger.info(' * 系统服务 {} 运行完成', Styled(self.name, Styles.CYAN))
            except CancelledError as e:
                raise e
            except:
                if not self.critical:
                    await logger.warning(' * 执行过程出现异常: {}', Styled(traceback.format_exc(), Styles.YELLOW))
                else:
                    await logger.critical(' * 关键执行过程出现异常: {}', Styled(traceback.format_exc(), Styles.RED))
                    raise RuntimeError("critical")


def service_task(
    name="undefined",
    descriptions="undefined",
    start_priority=-1,
    max_running_time=60,
    critical=False,
    trigger='start',
    *args,
    **kwargs
):
    def wrapper(func):
        def wrapped(*_, **__):
            return ServiceTask(name,
                               descriptions,
                               start_priority,
                               max_running_time,
                               critical,
                               trigger,
                               func,
                               *args,
                               **kwargs)
        return wrapped
    return wrapper


class ServiceRunner:
    def __init__(self, logger: Logger):
        self.service_list_on_start = []
        self.service_list_on_exit = []

        self.logger = logger
        self._lock = asyncio.Lock()

    async def add_service_task(self, service_task: ServiceTask):
        if type(service_task) is not ServiceTask:
            return False
        await self.logger.info('==============================注册系统服务==============================')
        await self.logger.info('服务名称: {}', Styled(service_task.name, Styles.CYAN))
        await self.logger.info('服务描述: {}', Styled(service_task.descriptions, Styles.CYAN))
        await self.logger.info('关键服务: {}', Styled('是', Styles.GREEN) if service_task.critical else Styled('否', Styles.BRIGHT_BLACK))
        await self.logger.info('优先等级: {}', Styled(service_task.start_priority, Styles.CYAN))
        await self.logger.info('触发方式: {}', Styled('启动时触发', Styles.CYAN) if service_task.trigger == 'start' else Styled('退出时触发', Styles.CYAN_BG, Styles.BLACK))
        await self.logger.info('超时时长: {} 秒', Styled(service_task.max_running_time, Styles.CYAN))
        async with self._lock:
            if service_task.trigger == 'start':
                self.service_list_on_start.append(
                    (service_task.start_priority, service_task.run))
            else:
                self.service_list_on_exit.append(
                    (service_task.start_priority, service_task.run))
        await self.logger.notice(Styled('注册系统服务 {} 成功', Styles.GREEN), Styled(service_task.name, Styles.CYAN))
        await self.logger.info('========================================================================')
        return True

    async def start(self):
        sorted_service_list = []
        async with self._lock:
            sorted_service_list = sorted(
                self.service_list_on_start, key=lambda x: x[0], reverse=True)

        async def iters():
            for item in sorted_service_list:
                yield item

        async for srv in iters():
            try:
                await srv[1](self.logger)
            except RuntimeError as e:
                raise e
            except CancelledError:
                return
            except:
                ...

    async def stop(self):
        sorted_service_list = []
        async with self._lock:
            sorted_service_list = sorted(
                self.service_list_on_exit, key=lambda x: x[0], reverse=True)

        async def iters():
            for item in sorted_service_list:
                yield item

        async for srv in iters():
            try:
                await srv[1](self.logger)
            except:
                ...
