import asyncio
import functools
import json
import os
import random
import re
from typing import Dict, Callable, List, Union, Any

import nonebot
import pytz
from aiocqhttp import MessageSegment
from nonebot import CQHttpError
from sqlitedict import SqliteDict

from yuiChyan import get_bot, YuiChyan, trigger, config, logger as bot_logger
from yuiChyan.exception import *
from yuiChyan.log import current_dir, new_logger
from yuiChyan.permission import NORMAL, PRIVATE, ADMIN, OWNER, SUPERUSER

# 服务配置
service_config_dir = os.path.abspath(os.path.join(current_dir, 'config', 'service_config'))
os.makedirs(service_config_dir, exist_ok=True)
loaded_services: Dict[str, 'Service'] = {}


# 异常拦截处理
def exception_handler(func) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        service_instance = args[0] if args else None
        try:
            return await func(*args, **kwargs)
        except BotException as e:
            if e.ev:
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
            visible: bool = True  # visible or not
    ):
        service_config = _read_service_config(name)
        self.name = name
        self.permission = service_config.get('permission') if service_config.get('permission') else permission
        self.manage = service_config.get('manage') if service_config.get('manage') else manage
        self.use_exclude = service_config.get('use_exclude') or use_exclude
        self.visible = service_config.get('visible') or visible
        self.include_group = service_config.get('include_group', [])
        self.exclude_group = service_config.get('exclude_group', [])
        logger = new_logger(name, config.DEBUG)

        self.logger = logger

        # 载入缓存
        assert self.name not in loaded_services, f'Service [{self.name}] is already exist!'
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
                raise ServiceEnabledException(f'Service [{self.name}] is already enabled at group [{group_id}]!')
            self.exclude_group.pop(group_id)
        else:
            if group_id in self.include_group:
                raise ServiceEnabledException(f'Service [{self.name}] is already enabled at group [{group_id}]!')
            self.include_group.append(group_id)
        _save_service_config(self)
        self.logger.info(f'Service [{self.name}] is enabled at group [{group_id}]')

    def disable_service(self, group_id: int):
        if self.use_exclude:
            if group_id in self.exclude_group:
                raise ServiceDisabledException(f'Service [{self.name}] is already disabled at group [{group_id}]!')
            self.exclude_group.append(group_id)
        else:
            if group_id not in self.include_group:
                raise ServiceDisabledException(f'Service [{self.name}] is already disabled at group [{group_id}]!')
            self.include_group.pop(group_id)
        _save_service_config(self)
        self.logger.info(f'Service [{self.name}] is disabled at group [{group_id}]')

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

    def on_message(self, event='group') -> Callable:
        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(ctx: CQEvent):
                if self.judge_enable(int(ctx.group_id)):
                    try:
                        return await func(self.bot, ctx)
                    except Exception as e:
                        self.logger.error(f'{type(e)} occurred when {func.__name__} handling message {ctx.message_id}.')
                        self.logger.exception(e)
                    return

            return self.bot.on_message(event)(wrapper)

        return deco

    def on_prefix(self, *prefix, only_to_me=False) -> Callable:
        if len(prefix) == 1 and not isinstance(prefix[0], str):
            prefix = prefix[0]

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(event):
                return await func(event)

            service_func = ServiceFunc(self, func, only_to_me)
            for p in prefix:
                if isinstance(p, str):
                    trigger.prefix.add(p, service_func)
                else:
                    self.logger.error(f'Failed to add prefix trigger [{p}], expecting [str] but [{type(p)}] given!')
            return func

        return deco

    def on_fullmatch(self, *word, only_to_me=False) -> Callable:
        if len(word) == 1 and not isinstance(word[0], str):
            word = word[0]

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(bot, event: CQEvent):
                if len(event.message) != 1 or event.message[0].data.get('text'):
                    self.logger.info(f'Message {event.message_id} is ignored by fullmatch condition.')
                    raise nonebot.command.SwitchException(nonebot.message.Message(event.raw_message))
                return await func(bot, event)

            service_func = ServiceFunc(self, wrapper, only_to_me)
            for w in word:
                if isinstance(w, str):
                    trigger.prefix.add(w, service_func)
                else:
                    self.logger.error(f'Failed to add fullmatch trigger [{w}], expecting [str] but [{type(w)}] given!')
            return func

        return deco

    def on_suffix(self, *suffix, only_to_me=False) -> Callable:
        if len(suffix) == 1 and not isinstance(suffix[0], str):
            suffix = suffix[0]

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(event):
                return await func(event)

            service_func = ServiceFunc(self, func, only_to_me)
            for s in suffix:
                if isinstance(s, str):
                    trigger.suffix.add(s, service_func)
                else:
                    self.logger.error(f'Failed to add suffix trigger [{s}], expecting [str] but [{type(s)}] given!')
            return func

        return deco

    def on_rex(self, rex: Union[str, re.Pattern], only_to_me=False, normalize=True) -> Callable:
        if isinstance(rex, str):
            rex = re.compile(rex)

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(event):
                return await func(event)

            sf = ServiceFunc(self, func, only_to_me, normalize)
            if isinstance(rex, re.Pattern):
                trigger.regular.add(rex, sf)
            else:
                self.logger.error(
                    f'Failed to add rex trigger [{str(rex)}] expecting [str] or [re.Pattern] but [{type(rex)}] given!')
            return func

        return deco

    def on_command(self, name, *, only_to_me=False, deny_tip=None, **kwargs) -> Callable:
        kwargs['only_to_me'] = only_to_me

        def deco(func) -> Callable:
            @functools.wraps(func)
            @exception_handler
            async def wrapper(session: nonebot.CommandSession):
                if session.ctx['message_type'] != 'group':
                    return
                if not self.judge_enable(int(session.ctx.group_id)):
                    self.logger.debug(f'Message {session.ctx.message_id} is command of a disabled service, ignored.')
                    if deny_tip:
                        await session.send(deny_tip, at_sender=True)
                    return
                try:
                    ret = await func(session)
                    self.logger.info(f'Message {session.ctx.message_id} is handled as command by {func.__name__}.')
                    return ret
                except (nonebot.message.CanceledException, nonebot.command.SwitchException) as e:
                    raise e
                except Exception as e:
                    self.logger.error(f'{type(e)} occurred when {func.__name__} '
                                      f'handling message {session.ctx.message_id}.')
                    self.logger.exception(e)

            return nonebot.on_command(name, **kwargs)(wrapper)

        return deco

    def scheduled_job(self, *args, **kwargs) -> Callable:
        kwargs.setdefault('timezone', pytz.timezone('Asia/Shanghai'))
        kwargs.setdefault('misfire_grace_time', 60)
        kwargs.setdefault('coalesce', True)

        def deco(func: Callable[[], Any]) -> Callable:
            @functools.wraps(func)
            async def wrapper():
                try:
                    self.logger.info(f'Scheduled job {func.__name__} start.')
                    ret = await func()
                    self.logger.info(f'Scheduled job {func.__name__} completed.')
                    return ret
                except Exception as e:
                    self.logger.error(f'{type(e)} occurred when doing scheduled job {func.__name__}.')
                    self.logger.exception(e)

            return nonebot.scheduler.scheduled_job(*args, **kwargs)(wrapper)

        return deco

    async def broadcast(self, msgs, tag='', interval_time=5, randomizer=None):
        bot = self.bot
        if isinstance(msgs, (str, MessageSegment, nonebot.message.Message)):
            msgs = (msgs,)
        groups = await self.get_enable_groups()
        group_dict = SqliteDict(
            os.path.join(os.path.dirname(__file__),
                         'plugins/authMS_lite/config/group.sqlite'),
            flag='r')
        for gid, self_id_list in groups.items():
            if gid not in group_dict:
                self.logger.error(f'群{gid} 投递{tag}失败：该群授权已过期')
                continue
            try:
                for msg in msgs:
                    await asyncio.sleep(interval_time)
                    msg = randomizer(msg) if randomizer else msg
                    await bot.send_group_msg(self_id=random.choice(self_id_list), group_id=gid, message=msg)
                length = len(msgs)
                if length:
                    self.logger.info(f'群{gid} 投递{tag}成功 共{length}条消息')
            except Exception as e:
                self.logger.error(f'群{gid} 投递{tag}失败：{type(e)}')
                self.logger.exception(e)


# 读取服务配置
def _read_service_config(service_name: str):
    config_file = os.path.join(service_config_dir, f'{service_name}.json')
    if not os.path.exists(config_file):
        return {}
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


# 保存服务配置
def _save_service_config(service: Service):
    config_file = os.path.join(service_config_dir, f'{service.name}.json')
    with open(config_file, 'w', encoding='utf8') as f:
        # noinspection PyTypeChecker
        json.dump(
            {
                'name': service.name,
                'permission': service.permission,
                'manage': service.manage,
                'use_exclude': service.use_exclude,
                'visible': service.visible,
                'include_group': service.include_group,
                'exclude_group': service.exclude_group
            },
            f,
            ensure_ascii=False,
            indent=4
        )


class ServiceFunc:
    def __init__(self, sv: 'Service', func: Callable, only_to_me: bool, normalize_text: bool = False):
        self.sv = sv
        self.func = func
        self.only_to_me = only_to_me
        self.normalize_text = normalize_text
        self.__name__ = func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


su_logger = new_logger('SU', config.DEBUG)


def su_command(name, force_private=True, **kwargs) -> Callable:
    kwargs['privileged'] = True
    kwargs['only_to_me'] = False

    def deco(func) -> Callable:
        @functools.wraps(func)
        async def wrapper(session: nonebot.CommandSession):
            if session.event.user_id not in config.SUPERUSERS:
                return
            if force_private and session.event.detail_type != 'private':
                await session.send('> This command should only be used in private session.')
                return
            try:
                return await func(session)
            except (nonebot.message.CanceledException, nonebot.command.SwitchException):
                raise
            except Exception as e:
                su_logger.error(f'{type(e)} occurred when {func.__name__} handling message {session.event.message_id}.')
                su_logger.exception(e)

        return nonebot.on_command(name, **kwargs)(wrapper)

    return deco
