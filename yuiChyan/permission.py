from aiocqhttp import Event as CQEvent

from yuiChyan import config

NORMAL = 1
PRIVATE = 10
ADMIN = 21
OWNER = 22
SUPERUSER = 999


def get_user_permission(ev: CQEvent):
    uid = ev.user_id
    if uid in config.SUPERUSERS:
        return SUPERUSER
    if ev['message_type'] == 'group':
        if not ev.anonymous:
            role = ev.sender.get('role')
            if role == 'member':
                return NORMAL
            elif role == 'admin':
                return ADMIN
            elif role == 'owner':
                return OWNER
        return NORMAL
    if ev['message_type'] == 'private':
        return PRIVATE
    return NORMAL


def check_permission(ev: CQEvent, require: int) -> bool:
    if ev['message_type'] == 'group':
        return get_user_permission(ev) >= require
    else:
        return False
