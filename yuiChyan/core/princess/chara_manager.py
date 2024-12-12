import json
import os
from typing import List, Dict, Union

import pygtrie
from PIL import Image
from fuzzywuzzy import process

from .util import sv, gadget_path, unit_path, chara_name_path, unavailable_chara_path
from yuiChyan.util import normalize_str


# 角色管理类
class CharaManager:
    def __init__(self):
        # 未知角色
        self.UNKNOWN_ID: int = 1000
        # 配置缓存
        self.CHARA_NAME: Dict[int, List[str]] = {}
        # 不可用角色缓存
        self.UNAVAILABLE_CHARA: Dict[int, List[str]] = {}
        # 加载角色
        self._load_pcr_data()
        # 未知角色名称
        self.UNKNOWN_NAME: List[str] = self.CHARA_NAME.get(self.UNKNOWN_ID)
        # 花名册
        self.roster: pygtrie.CharTrie = pygtrie.CharTrie()
        # 重载花名册
        self.reload_roster()

    # 加载数据
    def _load_pcr_data(self):
        # 加载角色
        with open(chara_name_path, 'r', encoding='utf-8') as f:
            chara_name_str = json.load(f)
        for _id in chara_name_str:
            self.CHARA_NAME[int(_id)] = chara_name_str[_id]

        # 加载NPC
        with open(unavailable_chara_path, 'r', encoding='utf-8') as f:
            unavailable_chara_str = json.load(f)
        for _id in unavailable_chara_str:
            self.UNAVAILABLE_CHARA[int(_id)] = unavailable_chara_str[_id]

    # 保存数据
    def _save_pcr_data(self):
        with open(chara_name_path, 'w+', encoding='utf-8') as f:
            # noinspection PyTypeChecker
            json.dump(self.CHARA_NAME, f, indent=4, ensure_ascii=False)

    # 重装花名册
    def reload_roster(self):
        self.roster.clear()
        for _id, names in self.CHARA_NAME.items():
            for n in names:
                n = normalize_str(n)
                if n not in self.roster:
                    self.roster[n] = _id
                else:
                    sv.logger.warning(f'PCR花名册: 角色ID [{_id}] 与 [{self.roster[n]}] 出现重名 [{n}]')

    # 新增角色 | 可传入名称或名称列表
    def add_chara_name(self, _id: int, names: Union[list, str]):
        name_get = self.CHARA_NAME.get(_id, [])
        if isinstance(names, str):
            name_get.append(names)
        elif isinstance(names, list):
            name_get += names
        else:
            pass
        self.CHARA_NAME[_id] = name_get
        self._save_pcr_data()

    # 根据名字获取ID
    def get_id(self, name: str) -> int:
        name = normalize_str(name)
        return self.roster[name] if name in self.roster else self.UNKNOWN_ID

    # 根据名字猜测 | 返回ID,名字。分数
    def guess_id(self, name: str) -> (int, str, int):
        name, score = process.extractOne(name, self.roster.keys(), processor=normalize_str)
        return self.roster[name], name, score

    # 根据队伍解析
    def parse_team(self, name_str) -> (List[int], str):
        name_str = normalize_str(name_str.strip())
        team: List[int] = []
        unknown: List[str] = []
        while name_str:
            item = self.roster.longest_prefix(name_str)
            if not item:
                unknown.append(name_str[0])
                name_str = name_str[1:].lstrip()
            else:
                team.append(item.value)
                name_str = name_str[len(item.key):].lstrip()
        return team, ''.join(unknown)


# 启动时加载一下
chara_manager = CharaManager()
# 各种基本图片资源加载一下
gadget_equip = Image.open(os.path.join(gadget_path, 'equip.png'))
gadget_star = Image.open(os.path.join(gadget_path, 'star.png'))
gadget_star_dis = Image.open(os.path.join(gadget_path, 'star_disabled.png'))
gadget_star_pink = Image.open(os.path.join(gadget_path, 'star_pink.png'))
unknown_chara_icon = Image.open(os.path.join(unit_path, f'icon_unit_{chara_manager.UNKNOWN_ID}31.png.png'))


# 是否是NPC
def is_npc(id_: int) -> bool:
    if id_ in chara_manager.UNAVAILABLE_CHARA:
        return True
    else:
        return not (1000 < id_ < 1900)
