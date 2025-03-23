import copy
import re
from typing import List, Iterable
from typing import TYPE_CHECKING

import pygtrie
import zhconv
from aiocqhttp import Event as CQEvent

import yuiChyan
from yuiChyan.util import normalize_str

if TYPE_CHECKING:
    from yuiChyan.service import ServiceFunc


# 基本触发器
class BaseTrigger:

    def add(self, x: str, sf: 'ServiceFunc'):
        pass

    def find_handler(self, ev: CQEvent) -> List['ServiceFunc']:
        pass

    # 转换简体
    @staticmethod
    def _convert_zh_hans(x: str) -> str:
        return zhconv.convert(x, 'zh-hans')

    # 添加触发器
    @staticmethod
    def _add(trie: pygtrie.CharTrie, x: str, sf: 'ServiceFunc'):
        x = BaseTrigger._convert_zh_hans(x)
        trie_list = trie.get(x, [])
        trie_list.append(sf)
        trie[x] = trie_list


# 前缀匹配触发器
class PrefixTrigger(BaseTrigger):

    def __init__(self):
        super().__init__()
        self.trie = pygtrie.CharTrie()

    def add(self, prefix_str: str, service_func: 'ServiceFunc'):
        super()._add(self.trie, prefix_str, service_func)
        yuiChyan.logger.debug(f'成功添加 [前缀匹配] 条件 [{prefix_str}]')

    def find_handler(self, ev: CQEvent) -> Iterable['ServiceFunc']:
        prefix_raw = ev.message[0]
        if prefix_raw.type != 'text':
            return
        prefix_str = super()._convert_zh_hans(prefix_raw.data['text'].lstrip())
        # 查找最长前缀
        step = self.trie.longest_prefix(prefix_str)
        if not step:
            return

        old_msg = copy.deepcopy(ev.message)
        ev['prefix'] = step.key
        prefix_str = prefix_str[len(step.key):].lstrip()
        if not prefix_str and len(ev.message) > 1:
            del ev.message[0]
        else:
            prefix_raw.data['text'] = prefix_str

        # 遍历匹配到的前缀对应的服务函数
        for service_func in step.value:
            yield service_func

        ev.message = old_msg


# 后缀匹配触发器
class SuffixTrigger(BaseTrigger):

    def __init__(self):
        super().__init__()
        self.trie = pygtrie.CharTrie()

    def add(self, suffix_str: str, service_func: 'ServiceFunc'):
        suffix_r = suffix_str[::-1]
        super()._add(self.trie, suffix_r, service_func)
        yuiChyan.logger.debug(f'成功添加 [后缀匹配] 条件 [{suffix_str}]')

    def find_handler(self, event: CQEvent) -> Iterable['ServiceFunc']:
        suffix_raw = event.message[-1]
        if suffix_raw.type != 'text':
            return
        suffix_str = super()._convert_zh_hans(suffix_raw.data['text'].rstrip())
        item = self.trie.longest_prefix(suffix_str[::-1])
        if not item:
            return

        old_msg = copy.deepcopy(event.message)
        event['suffix'] = item.key[::-1]
        last_text = suffix_str[: -len(item.key)].rstrip()
        if not last_text and len(event.message) > 1:
            del event.message[-1]
        else:
            suffix_raw.data['text'] = last_text

        for service_func in item.value:
            yield service_func

        event.message = old_msg


# 正则表达式匹配
class RegularTrigger(BaseTrigger):

    def __init__(self):
        super().__init__()
        self.regular_dict = {}

    def add(self, x: re.Pattern, sf: 'ServiceFunc'):
        trie_list = self.regular_dict.get(x, [])
        trie_list.append(sf)
        self.regular_dict[x] = trie_list
        yuiChyan.logger.debug(f'成功添加 [正则匹配] 条件 [{x.pattern}]')

    def find_handler(self, event: CQEvent) -> Iterable['ServiceFunc']:
        normal_text = normalize_str(str(event.message))
        event.normal_text = normal_text
        for rex, sfs in self.regular_dict.items():
            for service_func in sfs:
                match = rex.search(event.normal_text)
                if match:
                    event['match'] = match
                    yield service_func


# 四种基本匹配触发器
prefix = PrefixTrigger()
suffix = SuffixTrigger()
regular = RegularTrigger()

# 匹配触发链 | 优先级：前缀 > 后缀 > 正则
trigger_chain: List[BaseTrigger] = [
    prefix,
    suffix,
    regular
]
