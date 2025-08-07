import asyncio
import importlib
import os.path
from typing import List, LiteralString, Dict

import nonebot
from aiocqhttp import Message, MessageSegment
from jinja2 import FileSystemLoader
from nonebot import NoneBot, load_plugins, CQHttpError

import yuiChyan.config
from yuiChyan.config import ENABLE_AUTH
from yuiChyan.exception import *
from yuiChyan.log import new_logger
from yuiChyan.resources import *
from yuiChyan.trigger import trigger_chain


# 仅支持单个QQ号的YuiChyanBot
class YuiChyan(NoneBot):
    cached_self_id: Optional[int] = None
    cached_group_list: Optional[list] = None
    cache_lock = asyncio.Lock()

    def __init__(self, config_object=None):
        super().__init__(config_object)
        logger.info('> YuiChyanBot实例 启动成功')

    # 获取bot的QQ
    def get_self_id(self) -> int:
        if self.cached_self_id is None:
            qq_list = list(map(int, self._wsr_api_clients.keys()))
            if not qq_list:
                raise InterFunctionException('> 获取YuiChyan自身QQ号失败，可能是协议实现客户端未启动')
            self.cached_self_id = qq_list[0]
        return self.cached_self_id

    # 获取bot所加的群列表
    async def get_cached_group_list(self, use_cache: bool = True) -> list:
        async with self.cache_lock:
            if (not use_cache) or (self.cached_group_list is None):
                self_id = self.get_self_id()
                try:
                    self.cached_group_list = await yui_bot.get_group_list(self_id=self_id)
                except CQHttpError:
                    self.cached_group_list = []
            if not self.cached_group_list:
                raise InterFunctionException('> 获取YuiChyan群列表失败，可能是协议实现客户端未启动')
            return self.cached_group_list


# 全局唯一的BOT实例
yui_bot: Optional[YuiChyan] = None
# 全局默认的logger实例
logger = new_logger('YuiChyan', config.DEBUG)
# 插件帮助文档列表
help_list: List[Dict[str, LiteralString | str | bytes | int]] = []
# Quart资源路径
help_res_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'core', 'manager', 'help_res'))


# 获取当前BOT实例
def get_bot() -> YuiChyan:
    global yui_bot
    if yui_bot is None:
        raise YuiNotFoundException('YuiChyanBot实例还未启动!')
    return yui_bot


# 启动 YuiChyanBot 计时器
async def _start_scheduler():
    if nonebot.scheduler and not nonebot.scheduler.running:
        nonebot.scheduler.configure(config.APSCHEDULER_CONFIG)
        nonebot.scheduler.start()
        logger.info('> YuiChyanBot 核心计时器启动成功！')


# 创建 YuiChyanBot 实例
def create_instance() -> YuiChyan:
    global yui_bot

    config_logger = new_logger('config', config.DEBUG)
    config_logger.info("=== 开始加载核心配置 ===")
    importlib.import_module('yuiChyan.config')
    # 使用基础配置启动
    yui_bot = YuiChyan(config)

    # 配置 Quart App
    yui_bot.server_app.static_folder = os.path.join(help_res_dir, 'static')
    yui_bot.server_app.jinja_env.loader = FileSystemLoader(os.path.join(help_res_dir, 'template'))
    yui_bot.server_app.secret_key = os.urandom(24)
    # App 启动前载入计时器
    yui_bot.server_app.before_serving(_start_scheduler)

    # 加载插件
    _load_core_plugins(config_logger)
    _load_external_plugins(config_logger)
    config_logger.info("=== 所有插件加载完成 ===")

    # 装载消息处理触发器和处理器
    @_message_preprocessor
    async def _handle_message(bot: YuiChyan, event: CQEvent, _):
        await _process_message(bot, event)

    return yui_bot


# 加载核心插件
def _load_core_plugins(config_logger):
    config_logger.info("=== 开始加载核心插件 ===")
    for core_plugin in config.CORE_MODULE:
        load_plugins(str(os.path.join(os.path.dirname(__file__), 'core', core_plugin)),
                     f'yuiChyan.core.{core_plugin}')
        help_path = os.path.join(os.path.dirname(__file__), 'core', core_plugin, 'HELP.md')
        if os.path.exists(help_path):
            help_ = {
                'name': config.CORE_PLUGINS[core_plugin],
                'path': help_path,
            }
            help_list.append(help_)
        config_logger.info(f'> 核心插件 [{core_plugin}] 加载成功')


# 加载第三方插件
def _load_external_plugins(config_logger):
    config_logger.info("=== 开始加载拓展插件 ===")
    plugins_path = os.path.join(current_dir, 'plugins')
    if not os.path.exists(plugins_path):
        os.makedirs(plugins_path, exist_ok=True)
    for plugin_name in config.MODULES_ON:
        load_plugins(str(os.path.join(plugins_path, plugin_name)),
                     f'yuiChyan.plugins.{plugin_name}')
        help_path = os.path.join(plugins_path, plugin_name, 'HELP.md')
        if os.path.exists(help_path):
            help_ = {
                'name': config.EXTRA_PLUGINS[plugin_name],
                'path': help_path,
            }
            help_list.append(help_)
        config_logger.info(f'> 拓展插件 [{plugin_name}] 加载成功')


# 消息处理装饰器
def _message_preprocessor(func):
    mp = nonebot.message.MessagePreprocessor(func)
    nonebot.message.MessagePreprocessorManager.add_message_preprocessor(mp)
    return func


# 处理消息
async def _process_message(bot: YuiChyan, event: CQEvent):
    for _trigger in trigger_chain:
        for service_func in _trigger.find_handler(event):

            # 校验是否需要@触发
            if service_func.only_to_me and not event['to_me']:
                continue

            # 校验@的人是否是自己 | 如果@别人就不处理
            message_: Message[MessageSegment] = event.message
            seg_first: MessageSegment = message_[0]
            if seg_first.type == 'at' and str(seg_first.data['qq']) != str(event.self_id):
                continue

            # 如果有群ID
            if event.group_id:
                group_id = int(event.group_id)
                # 判断是否有授权
                if ENABLE_AUTH and service_func.sv.need_auth and group_id not in auth_db_:
                    continue
                # 群消息判断是否启用服务
                if not service_func.sv.judge_enable(group_id):
                    continue

            service_func.sv.logger.info(f'消息ID [{event.message_id}] 触发服务 [{service_func.__name__}]')
            try:
                await service_func.func(bot, event)
            except nonebot.command.SwitchException:
                continue
            except nonebot.message.CanceledException:
                raise
            except Exception as e:
                service_func.sv.logger.error(f'消息ID [{event.message_id}] 触发服务 [{service_func.__name__}] 出错：'
                                             f'{type(e)} {str(e)}')
                service_func.sv.logger.exception(e)
