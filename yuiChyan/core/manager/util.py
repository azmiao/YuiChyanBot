from datetime import timedelta, datetime

from rocksdict import Rdict

from yuiChyan import get_bot, FunctionException
from yuiChyan.config import NICKNAME, REMIND_BEFORE_EXPIRED
from yuiChyan.resources import auth_db_
from yuiChyan.service import Service

# BOT管理核心服务
sv = Service('core_manager', visible=False, need_auth=False, help_cmd='核心管理帮助')


# 获取数据库
async def get_database() -> Rdict:
    return auth_db_


# 获取授权结果列表
async def get_auth_group_list(self_id):
    # 所有的群
    group_list = await get_bot().get_cached_group_list()
    auth_db = await get_database()

    msg_list = []
    for group in group_list:
        group_id = group['group_id']
        group_name = group['group_name']
        expiration = auth_db.get(group_id, None)
        msg = await process_group_msg(self_id, group_id, group_name, expiration)
        msg_list.append(msg)
    return msg_list


# 生成群授权信息
async def process_group_msg(self_id, group_id, group_name, expiration, title: str = '', end: str = ''):
    # 没有群名就重新获取
    if not group_name:
        group_info = await get_bot().get_group_info(self_id=self_id, group_id=group_id)
        group_name = group_info['group_name']
    # 授权到期时间
    if expiration:
        time_format = expiration.strftime("%Y-%m-%d %H:%S:%M")
    else:
        time_format = '【未授权或已到期】'
    return f'{title}群名：{group_name}\n群号：{group_id}\n到期时间：{time_format}{end}'


# 通知群
async def group_notice(group_id, msg):
    await get_bot().send_group_msg(group_id=group_id, message=msg)


# 修改授权时间
async def change_authed_time(ev, group_id: int, time_change: int = 0):
    # 判断群是否在BOT列表里
    group_list = await get_bot().get_cached_group_list()
    group_id_list = [x['group_id'] for x in group_list]
    if group_id not in group_id_list:
        raise FunctionException(ev, f'群 [{str(group_id)}] 不存在，请检查！')
    # 判断群是否在数据库里
    auth_db = await get_database()
    if group_id in auth_db:
        auth_db[group_id] = auth_db[group_id] + timedelta(days=time_change)
    else:
        today = datetime.now()
        auth_db[group_id] = today + timedelta(days=time_change)
    return auth_db[group_id]


# 检查授权
async def check_auth():
    auth_db = await get_database()
    group_list = await get_bot().get_cached_group_list()
    for group in group_list:
        group_id = group['group_id']
        if group_id not in auth_db:
            continue
        sv.logger.info(f'> 正在检查群{group_id}的授权...')
        # 此群已有授权或曾有授权, 检查是否过期
        time_left = auth_db[group_id] - datetime.now()
        # 剩余天数
        days_left = time_left.days

        if time_left.total_seconds() <= 0:
            # 发消息提醒
            await group_notice(group_id, f'【提醒】本群授权已过期！\n如需续费请联系{NICKNAME}维护组~')
            # 清除授权
            auth_db.delete(group_id)
            sv.logger.info(f'群{group_id}的授权已过期，已清除对应授权信息')
        elif days_left < REMIND_BEFORE_EXPIRED:
            # 将要过期
            await group_notice(group_id, f'【提醒】本群的授权已不足{days_left + 1}天！\n如需续费请联系{NICKNAME}维护组~')
            sv.logger.info(f'群{group_id}的授权不足{days_left + 1}天')
