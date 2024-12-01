import re

from nonebot import on_notice, NoticeSession, on_request, RequestSession, CommandSession

from yuiChyan.service import su_command
from yuiChyan.util import *
from yuiChyan.config import NICKNAME


@on_notice('group_decrease.kick_me')
async def kick_me_alert(session: NoticeSession):
    group_id = session.event.group_id
    operator_id = session.event.operator_id
    super_id_list = config.SUPERUSERS
    for super_id in super_id_list:
        await session.bot.send_private_msg(
            self_id=session.event.self_id,
            user_id=super_id,
            message=f'YuiChyanBot[{session.event.self_id}]被群管理[{operator_id}]踢出群[{group_id}]')


@on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    ev = session.event
    name = ev.user_id
    if ev.user_id == ev.self_id:
        return
    try:
        info = await session.bot.get_stranger_info(self_id=ev.self_id, user_id=ev.user_id)
        name = info['nickname'] or name
        name = filter_message(str(name))
    except Exception as e:
        logger.exception(e)
    await session.send(f"{name}({ev.user_id})偷偷地退群了")


@on_request('group.invite')
async def handle_group_invite(session: RequestSession):
    if session.ctx.user_id in config.SUPERUSERS:
        await session.approve()
    else:
        await session.reject(reason=f'邀请{NICKNAME}入群请联系维护组哦~')


@su_command('quit', aliases='退群')
async def quit_group(session: CommandSession):
    if not session.current_arg_text:
        return
    group_id_list = session.current_arg_text.split(',')
    failed, success = [], []
    for group_id in group_id_list:
        if not re.fullmatch(r'^\d+$', group_id):
            failed.append(group_id)
            continue
        try:
            await session.bot.set_group_leave(self_id=session.event.self_id, group_id=int(group_id))
            success.append(group_id)
        except:
            failed.append(group_id)
    msg = f'> 已尝试退出{len(success)}个群'
    if failed:
        msg += f'\n失败{len(failed)}个群：{failed}'
    await session.send(msg)
