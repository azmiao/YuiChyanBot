import os
from typing import Dict, Any, List, Optional

import json5

# 注意：文件仅供内置核心插件配置读取用，默认情况下无法加载外置插件配置

# 基础配置
with open(os.path.join(os.path.dirname(__file__), 'base_config.json5'), 'r', encoding='utf-8') as _config:
    _data = json5.load(_config)
HOST: str = _data.get('HOST', '127.0.0.1')
PORT: int = _data.get('PORT', 2333)
DEBUG: bool = _data.get('DEBUG', False)
SUPERUSERS: List[int] = _data.get('SUPERUSERS', [])
NICKNAME: str = _data.get('NICKNAME', '')
PUBLIC_PROTOCOL: str = _data.get('PUBLIC_PROTOCOL', 'http')
PUBLIC_DOMAIN: Optional[str] = _data.get('PUBLIC_DOMAIN')
PROXY: Optional[str] = _data.get('PROXY', None)
CORE_PLUGINS: Dict[str, str] = _data.get('CORE_PLUGINS', {})
EXTRA_PLUGINS: Dict[str, str] = _data.get('EXTRA_PLUGINS', {})

# 授权管理系统
with open(os.path.join(os.path.dirname(__file__), 'auth_config.json5'), 'r', encoding='utf-8') as _config:
    _data = json5.load(_config)
ENABLE_AUTH: bool = _data.get('ENABLE_AUTH', True)
REMIND_BEFORE_EXPIRED: int = _data.get('REMIND_BEFORE_EXPIRED', 3)
GROUPS_IN_PAGE: int = _data.get('GROUPS_IN_PAGE', 5)
GROUP_LEAVE_MSG: str = _data.get('GROUP_LEAVE_MSG', '管理员操作')

# XQA
with open(os.path.join(os.path.dirname(__file__), 'xqa_config.json5'), 'r', encoding='utf-8') as _config:
    _data = json5.load(_config)
IS_SPILT_MSG: bool = _data.get('IS_SPILT_MSG', True)
MSG_LENGTH: int = _data.get('MSG_LENGTH', 1000)
SPLIT_INTERVAL: int = _data.get('SPLIT_INTERVAL', 1)
IS_FORWARD: bool = _data.get('IS_FORWARD', False)
IS_JUDGE_LENGTH: bool = _data.get('IS_JUDGE_LENGTH', False)
IS_DIRECT_SINGER: bool = _data.get('IS_DIRECT_SINGER', True)
SPLIT_MSG: str = _data.get('SPLIT_MSG', ' | ')
IS_BASE64: bool = _data.get('IS_BASE64', False)

# 其他默认配置
COMMAND_START = {''}
COMMAND_SEP = set()
APSCHEDULER_CONFIG: Dict[str, Any] = {
    'apscheduler.timezone': 'Asia/Shanghai',  # 执行计划任务时所用的时区
    'apscheduler.misfire_grace_time': 300,  # 宽限时间，如果任务的计划运行时间过去且未被调度，任务仍然可以在这个宽限期内执行
    'apscheduler.coalesce': True  # 在调度器未在正确时间运行时，同一任务被触发多次时，仅运行最后一个错过的任务
}
CORE_MODULE: List[str] = list(CORE_PLUGINS.keys())
MODULES_ON: List[str] = list(EXTRA_PLUGINS.keys())
