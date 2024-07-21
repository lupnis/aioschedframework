import asyncio

from shared import *

from data import ConfigLoader, Logger
from data.logs import LoggerConfig

from core.task_loader import TaskLoader
from core.service_loader import ServiceLoader

if __name__ == "__main__":
    mainloop = asyncio.new_event_loop()
    asyncio.set_event_loop(mainloop)

    config_path = './configs.json'
    ConstContainerClass.consts["config_path"] = config_path

    config = ConfigLoader(config_path)
    ConstContainerClass.consts["config"] = config.config
    EntityContainerClass.entities["config"] = config

    logger_config = {**LoggerConfig.DEFAULT_CONFIG,
                     **config.config.get("logger", {})}
    logger = Logger(logger_config)
    ConstContainerClass.consts["logger_config"] = logger_config
    EntityContainerClass.entities["logger"] = logger

    service_loader = ServiceLoader(logger)
    EntityContainerClass.entities["service_loader"] = service_loader

    task_loader = TaskLoader(logger)
    EntityContainerClass.entities["task_loader"] = task_loader

    service_config = config.config.get(
        "service_loader", {"path": "services"}).get("path", "services")
    ConstContainerClass.consts["service_config"] = service_config

    task_config = config.config.get(
        "task_loader", {"path": "tasks"}).get("path", "tasks")
    ConstContainerClass.consts["task_config"] = task_config

    def _call_exit():
        mainloop.run_until_complete(task_loader.stop())
        tasks = asyncio.all_tasks(mainloop)
        for task in tasks:
            task.cancel()
        mainloop.run_until_complete(service_loader.stop())
        mainloop.run_until_complete(logger.notice('系统已退出...'))
        quit(0)

    try:
        mainloop.run_until_complete(service_loader.load(service_config))
        mainloop.run_until_complete(service_loader.run())
        
        mainloop.run_until_complete(task_loader.load(task_config))
        mainloop.run_until_complete(task_loader.run())
        
        mainloop.run_forever()
    except KeyboardInterrupt:
        mainloop.run_until_complete(logger.notice('Ctrl + C 被按下, 系统退出中...'))
        _call_exit()
    except InterruptedError:
        mainloop.run_until_complete(logger.notice('接收到进程退出信号, 系统退出中...'))
        _call_exit()
    except RuntimeError:
        mainloop.run_until_complete(logger.critical('关键组件出现异常, 系统退出中...'))
        _call_exit()
    except:
        ...
