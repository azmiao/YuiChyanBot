from typing import Dict, Any

from .auth_config import *
from .base_config import *

# !!! 此文件的配置不建议调整 | 请去 `base_config.py` 里进行调整 !!!

COMMAND_START = {''}
COMMAND_SEP = set()
APSCHEDULER_CONFIG: Dict[str, Any] = {
    'apscheduler.timezone': 'Asia/Shanghai',  # 执行计划任务时所用的时区
    'apscheduler.misfire_grace_time': 60,  # 宽限时间，如果任务的计划运行时间过去且未被调度，任务仍然可以在这个宽限期内执行
    'apscheduler.coalesce': True  # 在调度器未在正确时间运行时，同一任务被触发多次时，仅运行最后一个错过的任务
}
CORE_MODULE = list(CORE_PLUGINS.keys())
MODULES_ON = list(EXTRA_PLUGINS.keys())
