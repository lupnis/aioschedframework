import importlib
import aiopath

from data.logs import Logger, Styled, Styles

from core.service_runner import ServiceRunner


class ServiceLoader:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.runner = ServiceRunner(self.logger)

    async def load(self, path='services'):
        await self.logger.info('开始读取系统服务...')
        cnt = 0
        async for task_module in aiopath.AsyncPath().glob(f'{path}/*.py'):
            mpath = str(task_module).replace('\\', '/')[:-3].replace('/', '.')
            try:
                imported = importlib.import_module(mpath)
                res = await self.runner.add_service_task(imported.run())
                if res:
                    cnt += 1
            except:
                ...
        await self.logger.notice('共加载 {} 个系统服务', Styled(cnt, Styles.CYAN))
        await self.logger.info(Styled('系统服务加载成功', Styles.GREEN))

    async def run(self):
        await self.logger.info(Styled('启动时系统服务启动成功', Styles.GREEN))
        await self.runner.start()
        
    async def stop(self):
        await self.logger.info(Styled('退出时系统服务启动成功', Styles.GREEN))
        await self.runner.stop()
