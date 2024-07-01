import importlib
import aiopath

from aiologging import Logger, Styled, Styles

from task_runner import Scheduler


class TaskLoader:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.scheduler = Scheduler(self.logger)

    async def load(self, path='tasks'):
        await self.logger.info('开始读取计划任务...')
        cnt = 0
        async for task_module in aiopath.AsyncPath().glob(f'{path}/*.py'):
            cnt += 1
            mpath = str(task_module).replace('\\', '/')[:-3].replace('/', '.')
            imported = importlib.import_module(mpath)
            
            await self.scheduler.add_scheduled_task(imported.run())
        await self.logger.notice('共加载 {} 个计划任务', Styled(cnt, Styles.CYAN))
        await self.logger.info(Styled('计划任务启动成功', Styles.GREEN))

    async def run(self):
        await self.scheduler.start()
