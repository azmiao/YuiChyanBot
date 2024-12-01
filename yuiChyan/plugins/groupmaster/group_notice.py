
import hoshino
from hoshino import service, util
from hoshino.typing import NoticeSession, CQHttpError

sv1 = Service('group-leave-notice', help_='退群通知')

@sv1.on_notice('group_decrease.leave')
async def leave_notice(session: NoticeSession):
    ev = session.event
    name = ev.user_id
    if ev.user_id == ev.self_id:
        return
    try:
        info = await session.bot.get_stranger_info(self_id=ev.self_id, user_id=ev.user_id)
        name = info['nickname'] or name
        name = util.filter_message(str(name))
    except CQHttpError as e:
        sv1.logger.exception(e)
    await session.send(f"{name}({ev.user_id})偷偷地退群了")


sv2 = Service('group-welcome', help_='入群欢迎')

@sv2.on_notice('group_increase')
async def increace_welcome(session: NoticeSession):
    if session.event.user_id == session.event.self_id:
        return  # ignore myself
    ev = session.event
    gid = session.event.group_id
    
    info = await session.bot.get_stranger_info(self_id=ev.self_id, user_id=ev.user_id)
    name = info['nickname'] if info['nickname'] else '未知'
    sex = info['sex']
    level = info['level']
    
    if sex == 'male':
        sex_info = '男'
    elif sex == 'female':
        sex_info = '女'
    else:
        sex_info = '已隐藏'

    msg = f'''
欢迎大佬入群！
昵称：{name}
QQ：{ev.user_id}
性别：{sex_info}
QQ等级：{level}

我是优衣酱~
回复“菜单”可以查看超多功能哦
    '''.strip()
    await session.send(msg, at_sender=True)