
# YuiBot未创建实例
class YuiNotFoundException(Exception):
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


# 服务已被开启过
class ServiceEnabledException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 服务已被关闭过
class ServiceDisabledException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 命令格式错误
class CommandErrorException(Exception):
    def __init__(self, message):
        super().__init__(message)


# 权限不足
class LakePermissionException(Exception):
    def __init__(self, message):
        super().__init__(message)