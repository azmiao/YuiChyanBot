import re
from math import ceil

from yuiChyan import YuiChyan, CQEvent
from yuiChyan.config import *
from .util import *


# 查询本群授权
@sv.on_match('查询授权')
async def query_group_auth(bot: YuiChyan, ev: CQEvent):
    if not ENABLE_AUTH:
        return
    group_id = ev.group_id
    self_id = ev.self_id
    auth_db = await get_database()
    if group_id in auth_db:
        msg = await process_group_msg(self_id, group_id, None, auth_db[group_id], title='> 授权查询结果\n')
    else:
        msg = '本群暂无任何授权，请联系维护组'
    await bot.send(ev, msg)


# 超管查询授权列表
@sv.on_command('授权列表', force_private=True)
async def auth_group_list(bot: YuiChyan, ev: CQEvent):
    if not ENABLE_AUTH:
        await bot.send(ev, '当前BOT未启用授权管理系统')
        return
    # 页数
    if not str(ev.message).strip():
        page = 1
    else:
        page = int(str(ev.message).strip())

    msg = '===== 授权列表 =====\n\n'
    auth_list = await get_auth_group_list(ev.self_id)
    length = len(auth_list)
    pages_all = ceil(length / GROUPS_IN_PAGE)
    if page > pages_all or page < 1:
        await bot.send(ev, f'请输入正确的页码, 当前共有授权信息{length}条, 共{pages_all}页')
        return

    start = (page - 1) * GROUPS_IN_PAGE
    end = min(page * GROUPS_IN_PAGE - 1, length)
    result_list = auth_list[start:end+1]
    msg += '\n\n'.join(result_list)
    msg += f'\n\n===== 当前页 {page}/{pages_all} ====='
    await bot.send(ev, msg)


# 超管查询好友列表
@sv.on_command('好友列表', force_private=True)
async def friend_list(bot: YuiChyan, ev: CQEvent):
    gl = await bot.get_friend_list(self_id=ev.self_id)
    msg_list = ['- {user_id}: {nickname}'.format_map(g) for g in gl]
    msg = f'> 共{len(gl)}个好友:\n' + '\n'.join(msg_list)
    await bot.send(ev, msg)


# 变更授权
@sv.on_command('变更授权', force_private=True)
async def modify_time_chat(bot: YuiChyan, ev: CQEvent):
    if not ENABLE_AUTH:
        await bot.send(ev, '当前BOT未启用授权管理系统')
        return
    origin = str(ev.message).strip()
    pattern = re.compile(r'^(\d{5,15})([+-]\d{1,5})$')
    m = pattern.match(origin)
    if m is None:
        await bot.send(ev, '请发送"授权 {群号}±{时长}"来进行指定群的授权, 时长最长为99999')
        return
    group_id = int(m.group(1))
    days = int(m.group(2))

    expiration = await change_authed_time(ev, group_id, days)
    msg = await process_group_msg(ev.self_id, group_id, None, expiration, title='变更成功, 变更后的群授权信息:\n')
    await group_notice(group_id, f'本群已增加{days}天授权时长，当前授权信息：\n{msg}')
    await bot.send(ev, msg)


# 立即执行一次检查
@sv.on_command('检查授权', force_private=True)
async def quick_check_chat(bot: YuiChyan, ev: CQEvent):
    if not ENABLE_AUTH:
        await bot.send(ev, '当前BOT未启用授权管理系统')
        return
    await check_auth()
    await bot.send(ev, '检查完成，请检查日志')


# 每天早上9点01检查授权
@sv.scheduled_job(day='*/1', hour='09', minute='01')
async def check_auth_schedule():
    if not ENABLE_AUTH:
        return
    await check_auth()
