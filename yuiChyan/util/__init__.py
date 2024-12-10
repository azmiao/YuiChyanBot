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
from .translator_lite.apis import Youdao

# 默认支持的语言
trans_dict = {
    'en': '英语',
    'zh': '中文',
    'ar': '阿拉伯语',
    'ru': '俄语',
    'fr': '法语',
    'de': '德语',
    'es': '西班牙语',
    'pt': '葡萄牙语',
    'it': '意大利语',
    'ja': '日语',
    'ko': '韩语',
    'nl': '荷兰语',
    'vi': '越南语',
    'id': '印尼语'
}
# 翻译器
_youdao = Youdao()

# 初始化敏感词
_search = StringSearch()
_sen_word_file = os.path.join(os.path.dirname(__file__), 'textfilter', 'sensitive_words.txt')
with open(_sen_word_file, 'r', encoding='utf-8') as f:
    _sen_word = f.read()
_search.SetKeywords(_sen_word.split('\n'))


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


# 规范化unicode字符串 并 转为小写 并 转为简体
def normalize_str(string) -> str:
    string = unicodedata.normalize('NFKC', string)
    string = string.lower()
    string = zhconv.convert(string, 'zh-hans')
    return string


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


# 敏感词替换
async def filter_message(message: Union[Message, str]):
    if isinstance(message, str):
        return _search.Replace(message)
    elif isinstance(message, Message):
        for seg in message:
            if seg.type == 'text':
                seg.data['text'] = _search.Replace(seg.data.get('text', ''))
        return message
    else:
        raise TypeError


# 翻译 | 目前只有有道引擎
async def translate(text: str, from_: str = 'auto', to_: str = 'zh') -> str:
    error_msg = ' - 目前支持的语言有：\n' + '\n'.join([f'{key}: {value}' for key, value in trans_dict.items()])
    assert from_ in trans_dict, f'源语言 [{from_}] 不存在\n{error_msg}'
    assert to_ in trans_dict, f'目标语言 [{to_}] 不存在\n{error_msg}'
    return _youdao.youdao_api(text, from_, to_)
