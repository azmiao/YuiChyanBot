import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
from aiocqhttp import Event as CQEvent
from aiocqhttp.exceptions import ActionFailed

import yuiChyan
from .common_code_utils import *
from .image_utils import *
from .translator import *


# 撤回消息
async def delete_msg(ev: CQEvent):
    try:
        await yuiChyan.get_bot().delete_msg(
            self_id=ev.self_id,
            message_id=ev.message_id
        )
    except ActionFailed as e:
        yuiChyan.logger.error(f'撤回失败: {e}')
    except Exception as e:
        yuiChyan.logger.exception(e)


# 禁言
async def silence(ev: CQEvent, ban_time, skip_su=True):
    try:
        if skip_su and ev.user_id in yuiChyan.config.SUPERUSERS:
            return
        await yuiChyan.get_bot().set_group_ban(
            self_id=ev.self_id,
            group_id=ev.group_id,
            user_id=ev.user_id,
            duration=ban_time
        )
    except ActionFailed as e:
        if 'NOT_MANAGEABLE' in str(e):
            return
        else:
            yuiChyan.logger.error(f'禁言失败 {e}')
    except Exception as e:
        yuiChyan.logger.exception(e)


# 频次限制器
class FreqLimiter:
    def __init__(self, default_cd_seconds):
        self.next_time = defaultdict(float)
        self.default_cd = default_cd_seconds

    def check(self, key) -> bool:
        return bool(time.time() >= self.next_time[key])

    def start_cd(self, key, cd_time=0):
        self.next_time[key] = time.time() + (cd_time if cd_time > 0 else self.default_cd)

    def left_time(self, key) -> float:
        return self.next_time[key] - time.time()


# 每日限制器
class DailyNumberLimiter:
    tz = pytz.timezone('Asia/Shanghai')

    def __init__(self, max_num):
        self.today = -1
        self.count = defaultdict(int)
        self.max = max_num

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        day = (now - timedelta(hours=5)).day
        if day != self.today:
            self.today = day
            self.count.clear()
        return bool(self.count[key] < self.max)

    def get_num(self, key):
        return self.count[key]

    def increase(self, key, num=1):
        self.count[key] += num

    def reset(self, key):
        self.count[key] = 0
