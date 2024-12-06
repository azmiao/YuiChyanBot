import random
import re

from nonebot import on_notice, NoticeSession, on_request, RequestSession

from yuiChyan.config import *
from yuiChyan.util import *
from .util import group_notice, sv


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


# 进群欢迎
@on_notice('group_increase')
async def group_welcome(session: NoticeSession):
    ev = session.event
    # 排除自己
    if ev.user_id == ev.self_id:
        return

    # 查询陌生人信息
    info = await session.bot.get_stranger_info(self_id=ev.self_id, user_id=ev.user_id)

    # 昵称
    name = info['nickname'] if info['nickname'] else '未知'
    # 性别
    match info['sex']:
        case 'male':
            sex_info = '男'
        case 'female':
            sex_info = '女'
        case _:
            sex_info = '已隐藏'

    msg = f'> 欢迎新大佬入群！\n昵称：{name}\nQQ：{ev.user_id}\n性别：{sex_info}\n\n> 我是{NICKNAME}~\n发送"菜单"可以查看功能列表哦'
    await session.send(msg, at_sender=True)


# 被邀请提示
@on_request('group.invite')
async def handle_group_invite(session: RequestSession):
    if session.ctx.user_id in SUPERUSERS:
        await session.approve()
    else:
        await session.reject(reason=f'邀请{NICKNAME}入群请联系维护组哦~')


# 主动退群命令
@sv.on_command('退群', force_private=True)
async def quit_group(bot, ev):
    strip = str(ev.message).strip()
    if not strip:
        await bot.send(ev, '命令错误，实例：退群 123456 管理员操作')
        return
    split = strip.split(' ')
    if not re.fullmatch(r'^\d+$', split[0]):
        await bot.send(ev, '命令错误，实例：退群 123456 管理员操作')
        return

    # 退群原因
    leave_reason = split[1] if split[1] else GROUP_LEAVE_MSG
    # 退群通知
    reason = f'> {NICKNAME}即将退出本群，感谢您的使用~\n退群原因:{leave_reason}'
    await group_notice(int(split[0]), reason)
    # 退群
    await bot.set_group_leave(self_id=ev.self_id, group_id=int(split[0]))
    msg = f'> 已成功退出群：{str(split[0])} | 原因：{leave_reason}'
    await bot.send(ev, msg)


# 让 YuiChyan 戳戳你
@sv.on_match(('戳一戳我', '戳戳我'), only_to_me=True)
async def send_point(bot, ev):
    await bot.send(ev, f'[CQ:poke,qq={int(ev.user_id)}]')


# YuiChyan 被戳提醒
@on_notice('notify.poke')
async def poke_back(session: NoticeSession):
    # 单次戳我的冷却
    time_limit = 10
    # 每日戳我的总上限
    daily_limit = 10
    # 返回的消息列表
    msg_list = [
        '呜喵~',
        '嗯哼？找优衣酱有啥事呢',
        '优衣酱饿了，能给我买点吃的吗~',
        '嘎哦~ 嘎哦~',
        '每天最多戳我十次哦~',
        '嗯...优衣酱..正在睡大觉呢',
        '看我的必杀技————花朵射击！',
        '喵喵喵？',
        '优衣酱我啊，以前可是优衣酱哦',
        '你戳的对，优衣酱我啊是由优衣酱自主研发的优衣酱',
        '大家要早睡早起哦，指第一天早上睡，第二天早上起',
        '俗话说的好，早期的虫儿被鸟吃',
        '欸嘿嘿，优衣酱打牌又赢了，荣！段幺九！',
        '优衣酱其实不是机器人，只是打字比较块而已，嗯'
    ]

    uid = session.ctx['user_id']
    self_ids = session.bot.get_self_ids()
    if session.ctx['target_id'] not in self_ids:
        return

    # 频次和单日次数检测
    lmt = FreqLimiter(time_limit)
    daily_limit = DailyNumberLimiter(daily_limit)
    if not lmt.check(uid):
        return
    if not daily_limit.check(uid):
        return

    lmt.start_cd(uid)
    daily_limit.increase(uid, 1)
    await session.send(random.choice(msg_list))
