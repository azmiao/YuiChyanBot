
from yuiChyan.service import Service as ParentService
from yuiChyan.permission import *


class Service(ParentService):
    def __init__(
            self,
            name: str,
            permission=NORMAL,
            manage=ADMIN,
            use_exclude: bool = True,
            visible: bool = True,
            enable_on_default: bool = True,
            help_: str = ""
    ):
        # 初始化父类构造函数
        super().__init__(name, permission, manage, use_exclude, visible)

        # 这些参数只是被接受，但不被使用
        self._ = enable_on_default
        self._ = help_
