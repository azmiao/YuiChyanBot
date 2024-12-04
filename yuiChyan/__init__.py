import importlib
from typing import List

import nonebot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import NoneBot, load_plugins

import yuiChyan.config
from yuiChyan.exception import *
from yuiChyan.log import *
from yuiChyan.trigger import trigger_chain


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


# 获取当前BOT实例
def get_bot() -> YuiChyan:
    global yui_bot
    if yui_bot is None:
        raise YuiNotFoundException('YuiChyan bot has not been created yet!')
    return yui_bot


# 启动nonebot计时器
async def _start_scheduler():
    scheduler = AsyncIOScheduler()
    if not scheduler.running:
        scheduler.configure(config.APSCHEDULER_CONFIG)
        scheduler.start()
        logger.debug('> YuiChyan scheduler started')


# 设置一些Nonebot的基础参数
def _set_default_config():
    config.COMMAND_START = {''}
    config.COMMAND_SEP = set()


# 创建 YuiChyanBot 实例
def create_instance() -> YuiChyan:
    global yui_bot

    # 使用基础配置启动
    _set_default_config()
    yui_bot = YuiChyan(config)
    yui_bot.server_app.before_serving(_start_scheduler)

    # 加载插件
    config_logger = new_logger('config', config.DEBUG)
    _load_core_plugins(config_logger)
    _load_external_plugins(config_logger)

    # 装载消息处理触发器和处理器
    @_message_preprocessor
    async def _handle_message(bot: YuiChyan, event: CQEvent, _):
        await _process_message(bot, event)

    return yui_bot


# 加载核心插件
def _load_core_plugins(config_logger):
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


# 加载第三方插件
def _load_external_plugins(config_logger):
    config_logger.info("=== Start to load external plugins ===")
    for plugin_name in config.MODULES_ON:
        try:
            importlib.import_module('yuiChyan.config.plugins.' + plugin_name)
            config_logger.info(f'> Succeeded to load external config of "{plugin_name}"')
        except ModuleNotFoundError:
            pass
        load_plugins(str(os.path.join(os.path.dirname(__file__), 'plugins', plugin_name)),
                     f'yuiChyan.plugins.{plugin_name}')
        config_logger.info(f'> Succeeded to load external plugin of "{plugin_name}"')
    config_logger.info("=== Plugin loading completed ===")


# 消息处理装饰器
def _message_preprocessor(func):
    mp = nonebot.message.MessagePreprocessor(func)
    nonebot.message.MessagePreprocessorManager.add_message_preprocessor(mp)
    return func


# 处理消息
async def _process_message(bot: YuiChyan, event: CQEvent):
    for _trigger in trigger_chain:
        for service_func in _trigger.find_handler(event):
            if service_func.only_to_me and not event['to_me']:
                continue

            if event.group_id:
                group_id = int(event.group_id)
                if not service_func.sv.judge_enable(group_id):
                    continue

            service_func.sv.logger.info(f'Message {event.message_id} triggered {service_func.__name__}.')
            try:
                await service_func.func(bot, event)
            except nonebot.command.SwitchException:
                continue
            except nonebot.message.CanceledException:
                raise
            except Exception as e:
                service_func.sv.logger.error(f'{type(e)} occurred when {service_func.__name__} '
                                             f'handling message {event.message_id}.')
                service_func.sv.logger.exception(e)
