import importlib
import aiopath

from data.logs import Logger, Styled, Styles

from core.task_runner import Scheduler


class TaskLoader:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.scheduler = Scheduler(self.logger)

    async def load(self, path='tasks'):
        await self.logger.info('开始读取计划任务...')
        cnt = 0
        async for task_module in aiopath.AsyncPath().glob(f'{path}/*.py'):
            mpath = str(task_module).replace('\\', '/')[:-3].replace('/', '.')
            try:
                imported = importlib.import_module(mpath)
                res = await self.scheduler.add_scheduled_task(imported.run())
                if res:
                    cnt += 1
            except:
                ...
        await self.logger.notice('共加载 {} 个计划任务', Styled(cnt, Styles.CYAN))
        await self.logger.info(Styled('计划任务加载成功', Styles.GREEN))

    async def run(self):
        await self.scheduler.start()
        await self.logger.info(Styled('计划任务启动成功', Styles.GREEN))
        
    async def stop(self):
        await self.logger.info('等待计划任务退出中...')
        await self.scheduler.stop()
        await self.logger.info(Styled('计划任务终止成功', Styles.GREEN))
