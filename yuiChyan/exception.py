from typing import Optional

from aiocqhttp import Event as CQEvent


# 基础异常
class BotException(Exception):
    def __init__(self, ev: Optional[CQEvent], message: str):
        super().__init__(message)
        self.ev = ev
        self.message = message


# YuiBot未创建实例
class YuiNotFoundException(BotException):
    def __init__(self, message):
        super().__init__(None, message)


# 手动抛出的业务异常 | 让BOT发送出去
class FunctionException(BotException):
    def __init__(self, ev: CQEvent, message: str):
        super().__init__(ev, message)


# 内部业务异常 | 无需BOT发送
class InterFunctionException(BotException):
    def __init__(self, message):
        super().__init__(None, message)


# session未找到
class SessionNotFoundException(BotException):
    def __init__(self, message):
        super().__init__(None, message)


# 同名session已经存在
class SessionExistException(BotException):
    def __init__(self, message):
        super().__init__(None, message)


# 服务已被开启
class ServiceEnabledException(BotException):
    def __init__(self, message):
        super().__init__(None, message)


# 服务已被关闭
class ServiceDisabledException(BotException):
    def __init__(self, message):
        super().__init__(None, message)


# 命令格式错误
class CommandErrorException(BotException):
    def __init__(self, message):
        super().__init__(None, message)


# 权限不足
class LakePermissionException(BotException):
    def __init__(self, ev: CQEvent, message):
        super().__init__(ev, message)


# 子功能被禁用
class SubFuncDisabledException(BotException):
    def __init__(self, message):
        super().__init__(None, message)
