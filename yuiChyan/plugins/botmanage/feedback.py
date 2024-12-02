import json
import re

import requests
from nonebot import on_command

import hoshino
import nonebot
from hoshino import service, priv
from hoshino.typing import CQEvent, MessageSegment
from hoshino.util import DailyNumberLimiter

sv_help = '''
- [#问题反馈] 后接反馈内容 联系维护组 请不要反馈无意义的事情
'''.strip()

sv = Service(
    name='问题反馈',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.SUPERUSER,  # 管理权限
    visible=False,  # False隐藏
    enable_on_default=True,  # 是否默认启用
    bundle='通用',  # 属于哪一类
    help_=sv_help  # 帮助文本
)


@sv.on_match(["问题反馈帮助"])
async def bangzhu(bot, ev):
    await bot.send(ev, sv_help, at_sender=True)


_max = 1
lmt = DailyNumberLimiter(_max)
EXCEED_NOTICE = f'您今天已经反馈过{_max}个问题了，不要折磨维护组了（'


@sv.on_prefix('#问题反馈')
async def feedback(bot, ev: CQEvent):
    uid = ev.user_id
    if not lmt.check(uid):
        await bot.finish(ev, EXCEED_NOTICE, at_sender=True)
    coffee = hoshino.config.SUPERUSERS[0]
    text = str(ev.message).strip()
    if not text:
        await bot.send(ev, "请发送#问题反馈+您要反馈的内容~", at_sender=True)
    else:
        await bot.send_private_msg(
            self_id=ev.self_id,
            user_id=coffee,
            message=f'【收到一条反馈信息】\n'
                    f'发送者:{uid}({get_name(uid)})\n发送群:{ev.group_id}\n反馈信息：{text}')
        await bot.send(ev, f'您的反馈已发送至维护组！\n======\n{text}', at_sender=True)
        lmt.increase(uid)


@on_command('【收到一条反馈信息】', only_to_me=False)
async def respond(session):
    origin = session.current_arg.strip()
    pattern = re.compile(r'^发送者:(\d+)[\s\S]+\s+?发送群:(\d+)\s+?反馈信息：([\s\S]*?)#([\s\S]*)$')
    results = pattern.match(origin)
    try:
        user, gid, problem, reply = results.group(1), results.group(2), \
                                    results.group(3).strip(), results.group(4).strip()
    except AttributeError:
        await session.finish("格式错误~")
        return
    if reply is None or not reply:
        await session.finish('请带上您要回应的内容~')
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        await session.finish('只有维护组才能使用该功能~')

    uid = session.event.user_id
    await nonebot.get_bot().send_group_msg(
        group_id=gid,
        message=f'【反馈的回复】\n提交者：{MessageSegment.at(user)}\n'
                f'反馈者：{get_name(uid)}\n'
                f'反馈详情：「{problem}」\n======\n回复：\n{reply}'
    )
    await session.finish(f'您的回复已发送至用户！\n======\n{reply}')


yui_bot = nonebot.get_bot()


@yui_bot.on_message("private.friend")
async def reply_feedback(ev):
    msg = ev.raw_message.strip()
    if not msg.startswith("[CQ:reply"):
        return
    try:
        args = re.search(r"(?i)\[cq:reply,[\s\S]+text=([\s\S]+)", msg).group(1).split("]")
    except AttributeError:
        await yui_bot.send(ev, "获取消息错误，请确认cqhttp配置")
        return
    origin_msg = args[0].strip()
    if not origin_msg.startswith("【收到一条反馈信息】"):
        return
    reply = args[1].strip()

    pattern = re.compile(r'^【收到一条反馈信息】\s+?发送者:(\d+)[\s\S]+\s+?发送群:(\d+)\s+?反馈信息：([\s\S]+)$')
    results = pattern.match(origin_msg)
    user, gid, problem = results.group(1), results.group(2), results.group(3)
    if ev.user_id not in hoshino.config.SUPERUSERS:
        await yui_bot.send(ev, '只有维护组才能使用该功能~')
        return

    uid = ev.user_id
    await yui_bot.send_group_msg(
        group_id=gid,
        message=f'【反馈的回复】\n提交者：{MessageSegment.at(user)}\n'
                f'反馈者：{get_name(uid)}\n'
                f'反馈详情：「{problem}」\n======\n回复：\n{reply}'
    )
    await yui_bot.send(ev, f'您的回复已发送至用户！\n======\n{reply}')
    return


def get_name(qq):
    if isinstance(qq, int):
        qq = str(qq)
    url = 'https://r.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg'
    params = {'uins': qq}
    res = requests.get(url, params=params)
    res.encoding = 'GBK'
    data_match = re.search(r'\{"%s":\[".+/%s/%s/.+]}' % (qq, qq, qq), res.text)
    if data_match:
        j_str = data_match.string
        j_str = j_str.split("portraitCallBack")[1].strip("(").strip(")")
        return json.loads(j_str)[qq][-2]
    else:
        return '神秘用户'