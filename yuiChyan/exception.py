from aiocqhttp import Event as CQEvent


# YuiBot未创建实例
class YuiNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 手动抛出的业务异常 | 让BOT发送出去
class FunctionException(Exception):
    def __init__(self, ev: CQEvent, message: str):
        super().__init__(message)


# 内部业务异常 | 无需BOT发送
class InterFunctionException(Exception):
    def __init__(self, message):
        super().__init__(message)


# session未找到
class SessionNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 同名session已经存在
class SessionExistException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 服务已被开启
class ServiceEnabledException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 服务已被关闭
class ServiceDisabledException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 命令格式错误
class CommandErrorException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 权限不足
class LakePermissionException(Exception):
    def __init__(self, ev: CQEvent, message):
        super().__init__(message)


# 子功能被禁用
class SubFuncDisabledException(Exception):
    def __init__(self, message):
        super().__init__(message)
