from typing import Optional

from aiocqhttp import Event as CQEvent

from yuiChyan.permission import Permission


# 基础异常
class BotException(Exception):
    def __init__(self, ev: Optional[CQEvent], message: Optional[str] = None, permission: Optional[Permission] = None):
        super().__init__(message)
        self.ev = ev
        self.message = message
        self.permission = permission


# YuiBot未创建实例
class YuiNotFoundException(BotException):
    def __init__(self, message: Optional[str] = None):
        self.message = message if message else 'YuiBot未创建实例'
        super().__init__(None, message)


# 手动抛出的业务异常 | 让BOT发送出去
class FunctionException(BotException):
    def __init__(self, ev: Optional[CQEvent], message: Optional[str] = None):
        self.message = message if message else '出现业务异常'
        super().__init__(ev, message)


# 内部业务异常 | 无需BOT发送
class InterFunctionException(BotException):
    def __init__(self, message: Optional[str] = None):
        self.message = message if message else '出现内部业务异常'
        super().__init__(None, message)


# session未找到
class SessionNotFoundException(BotException):
    def __init__(self, message: Optional[str] = None):
        self.message = message if message else 'Session未找到'
        super().__init__(None, message)


# 同名session已经存在
class SessionExistException(BotException):
    def __init__(self, message: Optional[str] = None):
        self.message = message if message else '同名Session已经存在'
        super().__init__(None, message)


# 命令格式错误
class CommandErrorException(BotException):
    def __init__(self, ev: Optional[CQEvent], message: Optional[str] = None):
        self.message = message if message else '命令格式错误'
        super().__init__(ev, message)


# 权限不足
class LakePermissionException(BotException):
    def __init__(self, ev: Optional[CQEvent], message: Optional[str] = None, permission: Optional[Permission] = None):
        # 没有消息内容，但有权限需求
        if permission and not message:
            message = f'您的权限不足，需要权限 [{permission.name}]'
        self.message = message if message else '命令格式错误'
        super().__init__(ev, message, permission)


# 子功能被禁用
class SubFuncDisabledException(BotException):
    def __init__(self, message: Optional[str] = None):
        self.message = message if message else '子功能被禁用'
        super().__init__(None, message)
