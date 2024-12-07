from functools import total_ordering

from aiocqhttp import Event as CQEvent

from yuiChyan import config


# 权限类
@total_ordering
class Permission:
    # 使用类变量存储所有权限实例
    _permissions_by_level = {}

    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level
        Permission._permissions_by_level[level] = self

    def __lt__(self, other):
        if not isinstance(other, Permission):
            return NotImplemented
        return self.level < other.level

    def __eq__(self, other):
        if not isinstance(other, Permission):
            return NotImplemented
        return self.level == other.level

    # 使用类方法从类变量中检索权限
    @classmethod
    def get_permission_by_level(cls, level: int) -> 'Permission':
        if level not in cls._permissions_by_level:
            raise Exception(f'权限级别 {level} 不存在，请检查')
        return cls._permissions_by_level.get(level)


# 权限级别
BLACK: Permission = Permission('黑名单', -999 )
NORMAL: Permission = Permission('群员', 1)
PRIVATE: Permission = Permission('私聊', 10)
ADMIN: Permission = Permission('群管理', 20)
OWNER: Permission = Permission('群主', 21)
SUPERUSER: Permission = Permission('维护组', 999)


# 根据事件获取用户权限
def get_user_permission(ev: CQEvent) -> Permission:
    uid = ev.user_id
    # 维护组
    if uid in config.SUPERUSERS:
        return SUPERUSER
    # 消息来源类型
    msg_type = ev['message_type']
    if msg_type == 'group':
        if ev.anonymous:
            return BLACK
        role = ev.get('sender', {}).get('role', '')
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
def check_permission(ev: CQEvent, require: Permission) -> bool:
    # 只对群聊做判断
    if ev['message_type'] == 'group':
        return get_user_permission(ev) >= require
    else:
        return False
