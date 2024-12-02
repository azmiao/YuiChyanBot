import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import unicodedata
import zhconv
from aiocqhttp import Event as CQEvent, Message, Union
from aiocqhttp.exceptions import ActionFailed

import yuiChyan
from .textfilter import *

# 初始化敏感词
search = StringSearch()
sen_word_file = os.path.join(os.path.dirname(__file__), 'textfilter', 'sensitive_words.txt')
with open(sen_word_file, 'r', encoding='utf-8') as f:
    sen_word = f.read()
search.SetKeywords(sen_word.split('\n'))


async def delete_msg(ev: CQEvent):
    try:
        await yuiChyan.get_bot().delete_msg(self_id=ev.self_id, message_id=ev.message_id)
    except ActionFailed as e:
        yuiChyan.logger.error(f'撤回失败: {e}')
    except Exception as e:
        yuiChyan.logger.exception(e)


async def silence(ev: CQEvent, ban_time, skip_su=True):
    try:
        if skip_su and ev.user_id in yuiChyan.config.SUPERUSERS:
            return
        await yuiChyan.get_bot().set_group_ban(self_id=ev.self_id, group_id=ev.group_id, user_id=ev.user_id, duration=ban_time)
    except ActionFailed as e:
        if 'NOT_MANAGEABLE' in str(e):
            return
        else:
            yuiChyan.logger.error(f'禁言失败 {e}')
    except Exception as e:
        yuiChyan.logger.exception(e)


def normalize_str(string) -> str:
    """
    规范化unicode字符串 并 转为小写 并 转为简体
    """
    string = unicodedata.normalize('NFKC', string)
    string = string.lower()
    string = zhconv.convert(string, 'zh-hans')
    return string


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


# 敏感词替换
def filter_message(message: Union[Message, str]):
    
    if isinstance(message, str):
        return search.Replace(message)
    elif isinstance(message, Message):
        for seg in message:
            if seg.type == 'text':
                seg.data['text'] = search.Replace(seg.data.get('text', ''))
        return message
    else:
        raise TypeError
