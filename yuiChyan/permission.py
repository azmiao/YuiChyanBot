from aiocqhttp import Event as CQEvent

from yuiChyan import config

BLACK = -999
NORMAL = 1
PRIVATE = 10
ADMIN = 21
OWNER = 22
SUPERUSER = 999


# 根据事件获取用户权限
def get_user_permission(ev: CQEvent):
    uid = ev.user_id
    # 维护组
    if uid in config.SUPERUSERS:
        return SUPERUSER
    # 消息来源类型
    msg_type = ev['message_type']
    if msg_type == 'group':
        if ev.anonymous:
            return BLACK
        role = ev.sender.get('role')
        match role:
            case 'owner':
                return OWNER
            case 'admin':
                return ADMIN
            case _:
                return NORMAL
    elif msg_type == 'private':
        return PRIVATE
    else:
        return BLACK


# 确认权限
def check_permission(ev: CQEvent, require: int) -> bool:
    # 只对群聊做判断
    if ev['message_type'] == 'group':
        return get_user_permission(ev) >= require
    else:
        return False
