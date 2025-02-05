import asyncio
import functools
import inspect
import os
import re
from logging import Logger
from typing import Dict, Callable, List, Union, Any, Tuple, Iterable

import nonebot
from apscheduler.triggers.cron import CronTrigger
from nonebot import CQHttpError

import yuiChyan.config
from yuiChyan import get_bot, YuiChyan, trigger, config, logger as bot_logger
from yuiChyan.exception import *
from yuiChyan.log import new_logger
from yuiChyan.permission import ADMIN, check_permission, Permission
from yuiChyan.resources import auth_db_ as auth_db, service_db_ as service_db
from yuiChyan.util.chart_generator import generate_image_from_markdown, convert_image_to_base64

# 全局服务配置缓存
_loaded_services: Dict[str, 'Service'] = {}


# 自定义异常拦截处理器
def exception_handler(func) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        service_instance = args[0] if args else None
        try:
            return await func(*args, **kwargs)
        except BotException as e:
            if e.ev and e.message:
                # 如果有事件和消息 | 将异常消息通过BOT发送
                await get_bot().send(e.ev, e.message, at_sender=True)
            else:
                # 优先使用 service_instance.logger 进行日志记录
                if service_instance and service_instance.logger:
                    service_instance.logger.error(e.message)
                else:
                    bot_logger.error(e.message)
            return

    return wrapper


# 服务实现类
class Service:

    def __init__(
            self,
            name: str,  # 服务名称
            manage: Permission = ADMIN,  # 管理启用和禁用的权限
            use_exclude: bool = True,  # 是否使用排除列表，即黑名单模式，否则使用白名单模式
            visible: bool = True,  # 是否在服务列表可见
            need_auth: bool = True,  # 是否需要群授权
            # 服务帮助文档命令，为空就不需要 | 通过service所在文件目录下的HELP.md生成图片
            help_cmd: Union[str, Tuple[str, ...], Iterable[str]] = None,
            help_at: bool = False  # 服务帮助文档命令是否需要@BOT触发
    ):
        self.name = name
        self.manage = manage
        self.use_exclude = use_exclude
        self.visible = visible
        self.need_auth = need_auth
        self.help_cmd = help_cmd
        self.help_at = help_at
        self.task_lock = asyncio.Lock()

        # sv实际的实例所在文件路径
        self.file_path: Optional[str] = None
        self.get_caller_file_path()

        # 内存中缓存的帮助图片字节
        self.help_bytes: Optional[bytes] = None

        service_config = _read_service_config(name)
        self.include_group: List[int] = service_config.get('include_group', [])
        self.exclude_group: List[int] = service_config.get('exclude_group', [])
        self.logger: Logger = new_logger(name, yuiChyan.config.DEBUG)

        # 载入缓存
        assert self.name not in _loaded_services, f'服务 [{self.name}] 已存在！'
        _loaded_services[self.name] = self

        # 帮助文档命令注册
        if self.help_cmd:
            @self.on_match(help_cmd, help_at)
            async def __get_help(bot, ev):
                await bot.send(ev, await self.__get_sv_help())

    # 获取bot
    @property
    def bot(self) -> YuiChyan:
        return get_bot()

    # 获取载入的所有服务缓存
    @staticmethod
    def get_loaded_services() -> Dict[str, 'Service']:
        return _loaded_services

    # 转化成简单的字符串字典
    def to_simple_dict(self, enable: bool = True) -> dict:
        return {
            'name': self.name,
            'manage': self.manage.name,
            'visible': self.visible,
            'need_auth': self.need_auth,
            'enable': enable
        }

    # 获取sv实际的实例所在文件路径
    def get_caller_file_path(self):
        # 获取调用栈
        stack = inspect.stack()
        # 获取调用Service的位置
        caller_frame = stack[2]
        self.file_path = caller_frame.filename

    # 获取自带的帮助
    async def __get_sv_help(self):
        help_path = os.path.join(os.path.dirname(self.file_path), 'HELP.md')
        if not os.path.exists(help_path):
            raise InterFunctionException('帮助文件 [HELP.md] 不存在，将忽略')

        if not self.help_bytes:
            with open(help_path, 'r', encoding='utf-8') as md_file:
                md_content = md_file.read()
            # 生成帮助图片
            self.help_bytes = await generate_image_from_markdown(md_content)

        # 转base64发送
        image_base64 = await convert_image_to_base64(self.help_bytes)
        return f'[CQ:image,file=base64://{image_base64}]'

    # 将自身服务保存至缓存
    def save_loaded_services(self):
        _loaded_services[self.name] = self

    # 对某个群开启服务
    def enable_service(self, group_id: int):
        if self.use_exclude:
            self.exclude_group.remove(group_id)
        else:
            self.include_group.append(group_id)
        self.save_loaded_services()
        _save_service_config(self)
        self.logger.info(f'服务 [{self.name}] 在群 [{group_id}] 启用成功！')

    # 对某个群禁用服务
    def disable_service(self, group_id: int):
        if self.use_exclude:
            self.exclude_group.append(group_id)
        else:
            self.include_group.remove(group_id)
        self.save_loaded_services()
        _save_service_config(self)
        self.logger.info(f'服务 [{self.name}] 在群 [{group_id}] 禁用成功！')

    # 判断某个群是否启用本服务
    def judge_enable(self, group_id: int) -> bool:
        if self.use_exclude:
            return group_id not in self.exclude_group
        else:
            return group_id in self.include_group

    # 获取所有启用本服务的群 | key: 群号 | value: BOT列表
    async def get_enable_groups(self) -> List[int]:
        try:
            self_group_list = await self.bot.get_cached_group_list()
        except CQHttpError:
            self_group_list = []
        self_group_list = list(int(x['group_id']) for x in self_group_list)
        if self.use_exclude:
            self_group_list = [item for item in self_group_list if item not in self.exclude_group]
        else:
            self_group_list = list(set(self_group_list) & set(self.include_group))
        return self_group_list

    def on_message(self, message_type: str = 'group') -> Callable:
        """
        > 服务触发 - 消息匹配 | 直接对消息进行匹配

        message_type: group为群消息事件，private为私聊消息事件等等，默认group
        """
        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(event: CQEvent):
                # 因为不走触发器，所以这里需要手动判断服务是否启用
                if self.judge_enable(int(event.group_id)):
                    try:
                        return await func(self.bot, event)
                    except Exception as e:
                        self.logger.exception(e)
                    return

            return self.bot.on_message(message_type)(wrapper)

        return deco

    def on_prefix(self, prefixes: Union[str, Tuple[str, ...], Iterable[str]],
                  only_to_me: bool = False) -> Callable:
        """
        > 服务触发 - 前缀匹配

        prefixes: 前缀

        only_to_me: 是否需要@BOT，默认不需要
        """
        if isinstance(prefixes, str):
            prefixes = (prefixes,)

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(bot, event: CQEvent):
                # 校验是否是群消息
                if event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(bot, event)

            service_func = ServiceFunc(self, wrapper, only_to_me)
            for prefix in prefixes:
                if isinstance(prefix, str):
                    trigger.prefix.add(prefix, service_func)
                else:
                    self.logger.error(f'前缀触发器 [{str(prefix)}] 添加失败，类型必须是 [str] 而不是 [{type(prefix)}]')
            return wrapper

        return deco

    def on_match(self, matches: Union[str, Tuple[str, ...], Iterable[str]],
                 only_to_me: bool = False) -> Callable:
        """
        > 服务触发 - 完全匹配

        matches: 匹配内容

        only_to_me: 是否需要@BOT，默认不需要
        """
        if isinstance(matches, str):
            matches = (matches,)

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(bot, event: CQEvent):
                # 校验是否是群消息
                if event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                # 带了其他字符就忽略
                if len(event.message) != 1 or event.message[0].data.get('text'):
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(bot, event)

            service_func = ServiceFunc(self, wrapper, only_to_me)
            for match in matches:
                if isinstance(match, str):
                    trigger.prefix.add(match, service_func)
                else:
                    self.logger.error(f'匹配触发器 [{str(match)}] 添加失败，类型必须是 [str] 而不是 [{type(match)}]')
            return wrapper

        return deco

    def on_suffix(self, suffixes: Union[str, Tuple[str, ...], Iterable[str]],
                  only_to_me: bool = False) -> Callable:
        """
        > 服务触发 - 后缀匹配

        suffixes: 后缀

        only_to_me: 是否需要@BOT，默认不需要
        """
        if isinstance(suffixes, str):
            suffixes = (suffixes,)

        def deco(func) -> Callable:
            @exception_handler
            @functools.wraps(func)
            async def wrapper(bot, event: CQEvent):
                # 校验是否是群消息
                if event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(bot, event)

            service_func = ServiceFunc(self, wrapper, only_to_me)
            for suffix in suffixes:
                if isinstance(suffix, str):
                    trigger.suffix.add(suffix, service_func)
                else:
                    self.logger.error(f'后缀触发器 [{str(suffix)}] 添加失败，类型必须是 [str] 而不是 [{type(suffix)}]')
            return wrapper

        return deco

    def on_rex(self, rex: Union[str, re.Pattern],
               only_to_me: bool = False) -> Callable:
        """
        > 服务触发 - 正则匹配

        rex: 正则表达式

        only_to_me: 是否需要@BOT，默认不需要
        """
        if isinstance(rex, str):
            rex = re.compile(rex)

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(bot, event: CQEvent):
                # 校验是否是群消息
                if event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(bot, event)

            service_func = ServiceFunc(self, wrapper, only_to_me)
            if isinstance(rex, re.Pattern):
                trigger.regular.add(rex, service_func)
            else:
                self.logger.error(f'正则触发器 [{str(rex)}] 添加失败，类型必须是 [str, re.Pattern] 而不是 [{type(rex)}]')
            return wrapper

        return deco

    def on_command(self, commands: Union[str, Tuple[str, ...], Iterable[str]],
                   only_to_me: bool = False,
                   force_private: bool = False,
                   cmd_permission: Permission = ADMIN) -> Callable:
        """
        > 服务触发 - 命令匹配

        commands: 命令

        only_to_me: 是否需要@BOT，默认不需要

        force_private: 是否强制私聊，如强制私聊则需维护组权限，默认不强制

        cmd_permission: 命令所需权限，默认群管理员
        """
        if isinstance(commands, str):
            commands = (commands,)

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(bot, event: CQEvent):
                # 私聊只支持超管 | 其他人的消息直接忽略
                if force_private and event.user_id not in config.SUPERUSERS:
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                # 校验是否是私聊
                if force_private and event.detail_type != 'private':
                    raise FunctionException(event, '> 该命令只支持私聊')
                if (not force_private) and event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                # 校验权限
                if (not force_private) and (not check_permission(event, cmd_permission)):
                    raise LakePermissionException(event, f'您的权限不足，需要权限 [{cmd_permission.name}]')
                return await func(bot, event)

            service_func = ServiceFunc(self, wrapper, only_to_me)
            for command in commands:
                if isinstance(command, str):
                    trigger.prefix.add(command, service_func)
                else:
                    self.logger.error(f'命令触发器 [{str(command)}] 添加失败，类型必须是 [str] 而不是 [{type(command)}]')
            return wrapper

        return deco

    def scheduled_job(self, silence: bool = False, **kwargs) -> Callable:
        """
        > 服务触发 - 定时任务

        silence: 是否沉默执行，不打印日志

        注意：参数只能是CronTrigger的参数

        定时任务的参数配置。
        """
        def deco(func: Callable[[], Any]) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper():
                # 异步锁 | 定时任务一个一个执行
                async with self.task_lock:
                    # 如果压根没有群启用了就直接跳过
                    group_self_list = await self.get_enable_groups()
                    # 排除授权过期的群
                    auth_group = [gid for gid in group_self_list if gid in auth_db]
                    if not auth_group:
                        self.logger.info(f'> 定时任务 {func.__name__} 已在所有群禁用或授权过期，将跳过执行')
                        return
                    if not silence:
                        self.logger.info(f'> 定时任务 {func.__name__} 开始运行...')
                    ret = await func()
                    if not silence:
                        self.logger.info(f'> 定时任务 {func.__name__} 执行完成！')
                    return ret

            # 使用 YuiChyanBot 生成的全局唯一计时器添加任务
            nonebot.scheduler.add_job(
                wrapper,
                CronTrigger(**kwargs),
                id=f'{self.name}_{func.__name__}_job',
                misfire_grace_time=300,
                replace_existing=True
            )

            return wrapper

        return deco

    async def broadcast(self, msgs: Union[str, Tuple[str, ...], Iterable[str]],
                        tag: str = '',
                        interval_time=5):
        """
        > 服务触发 - 广播消息

        msgs: 消息内容

        tag: 标签，默认无标签

        interval_time: 广播间隔，默认5秒
        """
        if isinstance(msgs, str):
            msgs = (msgs,)

        # 只对启用服务的群进行广播
        group_list = await self.get_enable_groups()
        for gid in group_list:
            if gid not in auth_db:
                self.logger.info(f'不会向群 [{gid}] 广播{tag}：该群授权已过期')
                continue
            try:
                for msg in msgs:
                    await asyncio.sleep(interval_time)
                    await self.bot.send_group_msg(self_id=self.bot.get_self_id(), group_id=gid, message=msg)
                length = len(msgs)
                if length:
                    self.logger.info(f'成功向群 [{gid}] 广播{tag}了 {length} 条消息')
            except Exception as e:
                self.logger.error(f'向群 [{gid}] 广播{tag}失败：{type(e)}')
                self.logger.exception(e)


# 读取服务配置
def _read_service_config(service_name: str):
    return service_db.get(service_name, {})


# 保存服务配置
def _save_service_config(service: Service):
    service_db[service.name] = {
        'name': service.name,
        'manage': service.manage,
        'use_exclude': service.use_exclude,
        'visible': service.visible,
        'need_auth': service.need_auth,
        'include_group': service.include_group,
        'exclude_group': service.exclude_group
    }


class ServiceFunc:
    def __init__(self, sv: 'Service', func: Callable, only_to_me: bool):
        self.sv = sv
        self.func = func
        self.only_to_me = only_to_me
        self.__name__ = func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
