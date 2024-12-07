import asyncio
import functools
import random
import re
from typing import Dict, Callable, List, Union, Any, Tuple, Iterable

import nonebot
from apscheduler.triggers.cron import CronTrigger
from nonebot import CQHttpError

import yuiChyan.config
from yuiChyan import get_bot, YuiChyan, trigger, config, logger as bot_logger
from yuiChyan.exception import *
from yuiChyan.log import new_logger
from yuiChyan.permission import NORMAL, PRIVATE, ADMIN, OWNER, SUPERUSER, check_permission
from yuiChyan.resources import auth_db_ as auth_db, service_db_ as service_db

# 全局服务配置缓存
loaded_services: Dict[str, 'Service'] = {}


# 自定义异常拦截处理器
def exception_handler(func) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        service_instance = args[0] if args else None
        try:
            return await func(*args, **kwargs)
        except BotException as e:
            if e.ev:
                # 将异常消息通过BOT发送
                await get_bot().send(e.ev, e.message)
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
            name: str,  # service name
            permission: NORMAL | PRIVATE | ADMIN | OWNER | SUPERUSER = NORMAL,  # use permission
            manage: NORMAL | PRIVATE | ADMIN | OWNER | SUPERUSER = ADMIN,  # manage permission
            use_exclude: bool = True,  # use exclude group: similar with blacklist, otherwise use whitelist
            visible: bool = True,  # visible or not
            need_auth: bool = True  # need bot auth
    ):
        service_config = _read_service_config(name)
        self.name = name
        self.permission = service_config.get('permission') if service_config.get('permission') else permission
        self.manage = service_config.get('manage') if service_config.get('manage') else manage
        self.use_exclude = service_config.get('use_exclude') or use_exclude
        self.visible = service_config.get('visible') or visible
        self.need_auth = service_config.get('need_auth') or need_auth
        self.include_group = service_config.get('include_group', [])
        self.exclude_group = service_config.get('exclude_group', [])
        self.logger = new_logger(name, yuiChyan.config.DEBUG)

        # 载入缓存
        assert self.name not in loaded_services, f'服务 [{self.name}] 已存在！'
        loaded_services[self.name] = self

    # 获取bot
    @property
    def bot(self) -> YuiChyan:
        return get_bot()

    @staticmethod
    def get_loaded_services() -> Dict[str, 'Service']:
        return loaded_services

    def enable_service(self, group_id: int):
        if self.use_exclude:
            if group_id not in self.exclude_group:
                raise ServiceEnabledException(f'服务 [{self.name}] 已经在群 [{group_id}] 中启用过了!')
            self.exclude_group.pop(group_id)
        else:
            if group_id in self.include_group:
                raise ServiceEnabledException(f'服务 [{self.name}] 已经在群 [{group_id}] 中启用过了!')
            self.include_group.append(group_id)
        _save_service_config(self)
        self.logger.info(f'服务 [{self.name}] 在群 [{group_id}] 开启成功！')

    def disable_service(self, group_id: int):
        if self.use_exclude:
            if group_id in self.exclude_group:
                raise ServiceDisabledException(f'服务 [{self.name}] 已经在群 [{group_id}] 中禁用过了!')
            self.exclude_group.append(group_id)
        else:
            if group_id not in self.include_group:
                raise ServiceDisabledException(f'服务 [{self.name}] 已经在群 [{group_id}] 中禁用过了!')
            self.include_group.pop(group_id)
        _save_service_config(self)
        self.logger.info(f'服务 [{self.name}] 在群 [{group_id}] 禁用成功！')

    def judge_enable(self, group_id: int) -> bool:
        if self.use_exclude:
            return group_id not in self.exclude_group
        else:
            return group_id in self.include_group

    async def get_enable_groups(self) -> Dict[int, List[int]]:
        group_self_dict = {}
        for self_id in self.bot.get_self_ids():
            try:
                self_group_list = await self.bot.get_group_list(self_id=self_id)
            except CQHttpError:
                self_group_list = []
            self_group_list = set(int(x['group_id']) for x in self_group_list)
            if self.use_exclude:
                self_group_list -= self.exclude_group
            else:
                self_group_list &= self.include_group
            for group in self_group_list:
                self_id_list = group_self_dict.get(group, [])
                self_id_list.append(self_id)
                group_self_dict[group] = self_id_list
        return group_self_dict

    def on_message(self, message_type: str = 'group') -> Callable:
        """
        > 服务触发 - 消息匹配 | 直接对消息进行匹配

        message_type: group为群消息事件，private为私聊消息事件等等，默认group
        """
        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(ctx: CQEvent):
                # 因为不走触发器，所以这里需要手动判断服务是否启用
                if self.judge_enable(int(ctx.group_id)):
                    try:
                        return await func(self.bot, ctx)
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
            async def wrapper(event):
                # 校验是否是群消息
                if event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(event)

            service_func = ServiceFunc(self, func, only_to_me)
            for prefix in prefixes:
                if isinstance(prefix, str):
                    trigger.prefix.add(prefix, service_func)
                else:
                    self.logger.error(f'前缀触发器 [{str(prefix)}] 添加失败，类型必须是 [str] 而不是 [{type(prefix)}]')
            return func

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
            return func

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
            async def wrapper(event):
                # 校验是否是群消息
                if event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(event)

            service_func = ServiceFunc(self, func, only_to_me)
            for suffix in suffixes:
                if isinstance(suffix, str):
                    trigger.suffix.add(suffix, service_func)
                else:
                    self.logger.error(f'后缀触发器 [{str(suffix)}] 添加失败，类型必须是 [str] 而不是 [{type(suffix)}]')
            return func

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
            async def wrapper(event):
                # 校验是否是群消息
                if event.detail_type != 'group':
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(event)

            service_func = ServiceFunc(self, func, only_to_me)
            if isinstance(rex, re.Pattern):
                trigger.regular.add(rex, service_func)
            else:
                self.logger.error(f'正则触发器 [{str(rex)}] 添加失败，类型必须是 [str, re.Pattern] 而不是 [{type(rex)}]')
            return func

        return deco

    def on_command(self, commands: Union[str, Tuple[str, ...], Iterable[str]],
                   only_to_me: bool = False,
                   force_private: bool = False,
                   cmd_permission: int = ADMIN) -> Callable:
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
                # 私聊只支持超管
                if force_private and event.user_id not in config.SUPERUSERS:
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                # 校验是否是私聊
                if force_private and event.detail_type != 'private':
                    raise FunctionException(event, '> 该命令只支持私聊')
                # 校验权限
                if not check_permission(event, cmd_permission):
                    raise LakePermissionException(event, '权限不足')
                return await func(bot, event)

            service_func = ServiceFunc(self, wrapper, only_to_me)
            for command in commands:
                if isinstance(command, str):
                    trigger.prefix.add(command, service_func)
                else:
                    self.logger.error(f'命令触发器 [{str(command)}] 添加失败，类型必须是 [str] 而不是 [{type(command)}]')
            return func

        return deco

    def scheduled_job(self, silence: bool = False, **kwargs) -> Callable:
        """
        > 服务触发 - 定时任务

        注意：参数只能是CronTrigger的参数

        定时任务的参数配置。
        """
        def deco(func: Callable[[], Any]) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper():
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

        bot = self.bot
        # 只对启用服务的群进行广播
        groups = await self.get_enable_groups()
        for gid, self_id_list in groups.items():
            if gid not in auth_db:
                self.logger.info(f'不会向群 [{gid}] 广播{tag}：该群授权已过期')
                continue
            try:
                for msg in msgs:
                    await asyncio.sleep(interval_time)
                    await bot.send_group_msg(self_id=random.choice(self_id_list), group_id=gid, message=msg)
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
        'permission': service.permission,
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
