import importlib
from typing import Optional, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import NoneBot, load_plugins

import yuiChyan.config
from yuiChyan.exception import *
from yuiChyan.log import *


class YuiChyan(NoneBot):

    def __init__(self, config_object=None):
        super().__init__(config_object)

    # 获取所有的bot的QQ
    def get_self_ids(self) -> List[int]:
        keys_as_int = map(int, self._wsr_api_clients.keys())
        return list(keys_as_int)


# 全局唯一的BOT实例
yui_bot: Optional[YuiChyan] = None
# 全局默认的logger实例
logger = new_logger('YuiChyan', config.DEBUG)


# 启动nonebot计时器
async def _start_scheduler():
    scheduler = AsyncIOScheduler()
    if not scheduler.running:
        scheduler.configure(config.APSCHEDULER_CONFIG)
        scheduler.start()
        logger.debug('> yuiChyan scheduler started')


def create_instance() -> YuiChyan:
    global yui_bot
    # 使用基础配置启动
    yui_bot = YuiChyan(config)
    yui_bot.server_app.before_serving(_start_scheduler)

    # 加载插件
    config_logger = new_logger('config', config.DEBUG)

    # 内置核心插件
    config_logger.info("=== Start to load core plugins ===")
    core_dir = os.path.join(current_dir, 'core')
    listdir = os.listdir(core_dir)
    for core_plugin in listdir:
        try:
            importlib.import_module('yuiChyan.config.' + core_plugin + '_config')
            config_logger.info(f'> Succeeded to load core config of "{core_plugin}_config"')
        except ModuleNotFoundError:
            pass
        load_plugins(str(os.path.join(os.path.dirname(__file__), 'core', core_plugin)),
                     f'yuiChyan.core.{core_plugin}')
        config_logger.info(f'> Succeeded to load core plugin of "{core_plugin}"')

    # 外置插件
    config_logger.info("=== Start to load plugins ===")
    for plugin_name in config.MODULES_ON:
        # 插件配置
        try:
            importlib.import_module('yuiChyan.config.plugins.' + plugin_name)
            config_logger.info(f'> Succeeded to load config of "{plugin_name}"')
        except ModuleNotFoundError:
            pass
        # 插件
        load_plugins(str(os.path.join(os.path.dirname(__file__), 'plugins', plugin_name)),
                     f'yuiChyan.plugins.{plugin_name}')
        config_logger.info(f'> Succeeded to load plugin of "{plugin_name}"')
    config_logger.info("=== Plugin loading completed ===")
    return yui_bot


# 获取当前BOT实例
def get_bot() -> YuiChyan:
    global yui_bot
    if yui_bot is None:
        raise YuiNotFoundException('yuiChyan bot has not been created yet!')
    return yui_bot
