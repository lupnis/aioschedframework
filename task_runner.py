import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
from aiologging import Logger, Styled, Styles
import croniter
import gc
import functools
import traceback
import inspect
import aiopath


class ScheduledTask:
    def __init__(self, name="undefined",
                 descriptions="undefined",
                 cron="* * * * *",
                 single_shot=False,
                 max_running_time=60,
                 func=None,
                 *args,
                 **kwargs):
        self.name = name
        self.descriptions = descriptions
        self.cron = cron
        self.single_shot = single_shot
        self.max_running_time = max_running_time
        self.func = func
        self.running_args = args
        self.running_kwargs = kwargs

    async def run(self, manager, logger):
        if self.func:
            res = 0
            path = aiopath.AsyncPath(inspect.getfile(self.func))
            home = aiopath.AsyncPath('.').absolute()
            await logger.info('==============================执行计划任务==============================')
            await logger.info('任务名称: {}', Styled(self.name, Styles.CYAN))
            await logger.info('任务描述: {}', Styled(self.descriptions, Styles.CYAN))
            await logger.info('周期执行: {}', Styled('是', Styles.GREEN) if not self.single_shot else Styled('否', Styles.BRIGHT_BLACK))
            await logger.info('超时时长: {} 秒', Styled(self.max_running_time, Styles.CYAN))
            await logger.info('周期信息: {}', Styled(self.cron, Styles.CYAN))
            await logger.info('执行函数: {}', Styled(path.relative_to(home), Styles.CYAN))
            try:
                res = await asyncio.wait_for(self.func(*self.running_args, **self.running_kwargs, logger=logger), self.max_running_time)
            except Exception as e:
                await logger.warning('执行过程出现异常: {}', Styled(traceback.format_exc(), Styles.YELLOW))
        if not self.single_shot and res == 0:
            await manager.register_new_turn(self)
            gc.collect()
        await logger.info('========================================================================')


def scheduled_task(
    name,
    descriptions,
    cron="* * * * *",
    single_shot=False,
    max_running_time=60,
    *args,
    **kwargs
):
    def wrapper(func):
        def wrapped(*_, **__):
            return ScheduledTask(name,
                                 descriptions,
                                 cron,
                                 single_shot,
                                 max_running_time,
                                 func,
                                 *args,
                                 **kwargs)
        return wrapped
    return wrapper


class Scheduler:
    def __init__(self, logger: Logger):
        self.scheduler = AsyncIOScheduler()
        self.logger = logger

    async def add_scheduled_task(self, scheduled_task: ScheduledTask):
        path = aiopath.AsyncPath(inspect.getfile(scheduled_task.func))
        home = aiopath.AsyncPath('.').absolute()
        await self.logger.info('==============================注册计划任务==============================')
        await self.logger.info('任务名称: {}', Styled(scheduled_task.name, Styles.CYAN))
        await self.logger.info('任务描述: {}', Styled(scheduled_task.descriptions, Styles.CYAN))
        await self.logger.info('周期执行: {}', Styled('是', Styles.GREEN) if not scheduled_task.single_shot else Styled('否', Styles.BRIGHT_BLACK))
        await self.logger.info('超时时长: {} 秒', Styled(scheduled_task.max_running_time, Styles.CYAN))
        await self.logger.info('周期信息: {}', Styled(scheduled_task.cron, Styles.CYAN))
        await self.logger.info('执行函数: {}', Styled(path.relative_to(home), Styles.CYAN))
        try:
            current_time = datetime.datetime.now()
            cron = croniter.croniter(scheduled_task.cron, current_time)
            next_time = cron.get_next(datetime.datetime)
            self.scheduler.add_job(functools.partial(
                scheduled_task.run, self, self.logger), next_run_time=next_time)
            await self.logger.notice(Styled('注册计划任务 {} 成功, 下次执行时间: {}', Styles.GREEN), Styled(scheduled_task.name, Styles.CYAN), Styled(next_time, Styles.CYAN))
        except Exception as e:
            print(e)
            await self.logger.warning(Styled('注册计划任务 {} 失败!', Styles.RED), Styled(scheduled_task.name, Styles.CYAN))
        await self.logger.info('========================================================================')

    async def register_new_turn(self, scheduled_task: ScheduledTask):
        try:
            current_time = datetime.datetime.now()
            cron = croniter.croniter(scheduled_task.cron, current_time)
            next_time = cron.get_next(datetime.datetime)
            self.scheduler.add_job(functools.partial(
                scheduled_task.run, self, self.logger), next_run_time=next_time)
        except:
            pass

    async def start(self):
        self.scheduler.start()
