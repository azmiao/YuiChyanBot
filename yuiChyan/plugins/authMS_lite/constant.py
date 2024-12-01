import os

import hoshino
from sqlitedict import SqliteDict

__version__ = '0.2.1.6-lite'

# noinspection PyBroadException
try:
    config = hoshino.config.authMS_lite.AuthConfig
except:
    # 保不准哪个憨憨又不读README呢
    hoshino.logger.error('authMS无配置文件!请仔细阅读README')

group_dict = SqliteDict(os.path.join(os.path.dirname(__file__), 'config/group.sqlite'), autocommit=True)
trial_list = SqliteDict(os.path.join(os.path.dirname(__file__), 'config/trial.sqlite'), autocommit=True)  # 试用列表
