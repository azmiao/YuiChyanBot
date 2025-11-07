import html
import os

import unicodedata
import zhconv
from aiocqhttp import Message, Union

from .textfilter import *

# 初始化敏感词
_search = StringSearch()
_sen_word_file = os.path.join(os.path.dirname(__file__), 'textfilter', 'sensitive_words.txt')
with open(_sen_word_file, 'r', encoding='utf-8') as f:
    _sen_word = f.read()
_search.SetKeywords(_sen_word.split('\n'))

# 敏感词替换
async def filter_message(message: Union[Message, str]) -> Union[Message, str]:
    if isinstance(message, str):
        return _search.Replace(message)
    elif isinstance(message, Message):
        for seg in message:
            if seg.type == 'text':
                seg.data['text'] = _search.Replace(seg.data.get('text', ''))
        return message
    else:
        raise TypeError


# 规范化unicode字符串 并 转为简体
def normalize_str(string) -> str:
    string = unicodedata.normalize('NFKC', string)
    string = html.unescape(string)
    string = zhconv.convert(string, 'zh-hans')
    return string


# 自动截断字符串
def truncate_string(s: str, max_length: int = 8) -> str:
    if len(s) > max_length:
        return s[:max_length] + '...'
    return s
