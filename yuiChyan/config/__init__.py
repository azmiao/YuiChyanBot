import os
from typing import Dict, Any

from .auth_config import *
from .based_config import *

current_dir = os.path.dirname(os.path.dirname(__file__))
# 资源文件夹
RES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'res')
# 计时器配置
APSCHEDULER_CONFIG: Dict[str, Any] = {'apscheduler.timezone': 'Asia/Shanghai'}
