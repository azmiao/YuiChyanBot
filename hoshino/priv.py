
from yuiChyan.permission import *


def get_user_priv(ev):
    return get_user_permission(ev).level


def check_priv(ev, require: int):
    # 只对群聊做判断
    if ev['message_type'] == 'group':
        return get_user_permission(ev).level >= require
    else:
        return False
