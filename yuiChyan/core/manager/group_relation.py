import re

from nonebot import on_notice, NoticeSession, on_request, RequestSession, CommandSession

from yuiChyan.config import *
from yuiChyan.service import su_command
from yuiChyan.util import *
from .util import group_notice


# 被踢提醒
@on_notice('group_decrease.kick_me')
async def kick_me_alert(session: NoticeSession):
    group_id = session.event.group_id
    operator_id = session.event.operator_id
    super_id_list = SUPERUSERS
    for super_id in super_id_list:
        await session.bot.send_private_msg(
            self_id=session.event.self_id,
            user_id=super_id,
            message=f'YuiChyanBot[{session.event.self_id}]被群管理[{operator_id}]踢出群[{group_id}]')


# 群员退群提醒
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
        yuiChyan.logger.exception(e)
    await session.send(f"{name}({ev.user_id})偷偷地退群了")


# 被邀请提示
@on_request('group.invite')
async def handle_group_invite(session: RequestSession):
    if session.ctx.user_id in SUPERUSERS:
        await session.approve()
    else:
        await session.reject(reason=f'邀请{NICKNAME}入群请联系维护组哦~')


# 主动退群命令
@su_command('退群')
async def quit_group(session: CommandSession):
    strip = str(session.current_arg_text).strip()
    if not strip:
        await session.send('命令错误，实例：退群 123456 管理员操作')
        return
    split = strip.split(' ')
    if not re.fullmatch(r'^\d+$', split[0]):
        await session.send('命令错误，实例：退群 123456 管理员操作')
        return

    # 退群原因
    leave_reason = split[1] if split[1] else GROUP_LEAVE_MSG
    # 退群通知
    reason = f'> {NICKNAME}即将退出本群，感谢您的使用~\n退群原因:{leave_reason}'
    await group_notice(int(split[0]), reason)
    # 退群
    await session.bot.set_group_leave(self_id=session.event.self_id, group_id=int(split[0]))
    msg = f'> 已成功退出群：{str(split[0])} | 原因：{leave_reason}'
    await session.send(msg)
