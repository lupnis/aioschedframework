from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from asyncio.exceptions import CancelledError
import croniter
import datetime
import gc
import traceback

from data import Logger
from data.logs import Styled, Styles


class ScheduledTask:
    def __init__(self, name="undefined",
                 descriptions="undefined",
                 cron="* * * * *",
                 single_shot=False,
                 max_running_time=60,
                 run_after_create=False,
                 func=None,
                 *args,
                 **kwargs):
        self.name = name
        self.descriptions = descriptions
        self.cron = cron
        self.single_shot = single_shot
        self.max_running_time = max_running_time
        self.run_after_create = run_after_create
        self.func = func
        self.running_args = args
        self.running_kwargs = kwargs
        self.logger = None
        self.manager = None

    async def run(self):
        if self.func and self.logger:
            res = 0
            await asyncio.gather(
                self.logger.info(
                    '==============================执行计划任务=============================='),
                self.logger.info(
                    ' * 任务名称: {}', Styled(self.name, Styles.CYAN)),
                self.logger.info(' * 任务描述: {}',
                                 Styled(self.descriptions, Styles.CYAN)),
                self.logger.info(' * 周期执行: {}', Styled('是', Styles.GREEN)
                                 if not self.single_shot else Styled('否', Styles.BRIGHT_BLACK)),
                self.logger.info(' * 超时时长: {} 秒',
                                 Styled(self.max_running_time, Styles.CYAN)),
                self.logger.info(
                    ' * 周期信息: {}', Styled(self.cron, Styles.CYAN))
            )
            try:
                res = await asyncio.wait_for(self.func(*self.running_args, **self.running_kwargs, logger=self.logger), self.max_running_time)
            except TimeoutError:
                await self.logger.warning(' * 计划任务 {} 运行超时, 已停止', Styled(self.name, Styles.CYAN))
                gc.collect()
            except CancelledError:
                return
            except:
                await self.logger.warning(' * 执行过程出现异常: {}', Styled(traceback.format_exc(), Styles.YELLOW))
            if not self.single_shot and res == 0 and self.manager:
                await self.manager.register_new_turn(self)
                gc.collect()
            await self.logger.info(' * 计划任务 {} 运行完成', Styled(self.name, Styles.CYAN))


def scheduled_task(
    name,
    descriptions,
    cron="* * * * *",
    single_shot=False,
    max_running_time=60,
    run_after_create=False,
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
                                 run_after_create,
                                 func,
                                 *args,
                                 **kwargs)
        return wrapped
    return wrapper


class Scheduler:
    def __init__(self, logger: Logger, max_workers=8):
        self.scheduler = AsyncIOScheduler(
            job_defaults={'misfire_grace_time': 15 * 60},
            executors={'processpool': ProcessPoolExecutor(max_workers)})
        self.logger = logger

    async def add_scheduled_task(self, scheduled_task: ScheduledTask):
        if type(scheduled_task) is not ScheduledTask:
            return False
        flag = True
        await self.logger.info('==============================注册计划任务==============================')
        await self.logger.info('任务名称: {}', Styled(scheduled_task.name, Styles.CYAN))
        await self.logger.info('任务描述: {}', Styled(scheduled_task.descriptions, Styles.CYAN))
        await self.logger.info('周期执行: {}', Styled('是', Styles.GREEN) if not scheduled_task.single_shot else Styled('否', Styles.BRIGHT_BLACK))
        await self.logger.info('超时时长: {} 秒', Styled(scheduled_task.max_running_time, Styles.CYAN))
        await self.logger.info('周期信息: {}', Styled(scheduled_task.cron, Styles.CYAN))
        scheduled_task.logger = self.logger
        scheduled_task.manager = self
        try:
            current_time = datetime.datetime.now()
            cron = croniter.croniter(scheduled_task.cron, current_time)
            next_time = cron.get_next(
                datetime.datetime) if not scheduled_task.run_after_create else current_time
            self.scheduler.add_job(scheduled_task.run, next_run_time=next_time)
            await self.logger.notice(Styled('注册计划任务 {} 成功, 首次执行计划时间: {}', Styles.GREEN), Styled(scheduled_task.name, Styles.CYAN), Styled(next_time, Styles.CYAN))
        except:
            flag = False
            await self.logger.warning(Styled('注册计划任务 {} 失败!', Styles.RED), Styled(scheduled_task.name, Styles.CYAN))
        await self.logger.info('========================================================================')
        return flag

    async def register_new_turn(self, scheduled_task: ScheduledTask):
        try:
            current_time = datetime.datetime.now()
            cron = croniter.croniter(scheduled_task.cron, current_time)
            next_time = cron.get_next(datetime.datetime)
            self.scheduler.add_job(scheduled_task.run, next_run_time=next_time)
            return True
        except:
            return False

    async def start(self):
        self.scheduler.start()

    async def stop(self):
        try:
            self.scheduler.shutdown(True)
        except:
            ...
