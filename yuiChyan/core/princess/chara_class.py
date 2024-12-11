import json
import os

from PIL import Image

from .util import gadget_path, unit_path, current_dir

# 未知角色
UNKNOWN = 1000
# 配置缓存
CHARA_NAME = {}
UnavailableChara = {}


# 角色类
class CharaMaster:
    def __init__(self) -> None:
        self.chara_name_path = os.path.join(current_dir, 'CHARA_NAME.json')
        self.unavailable_chara_path = os.path.join(current_dir, 'UnavailableChara.json')
        self.__load_pcr_data()

    # 加载数据
    def __load_pcr_data(self) -> None:
        with open(self.chara_name_path, 'r', encoding='utf-8') as f:
            chara_name_str = json.load(f)
        global CHARA_NAME
        for _id in chara_name_str:
            CHARA_NAME[int(_id)] = chara_name_str[_id]

        with open(self.unavailable_chara_path, 'r', encoding='utf-8') as f:
            unavailable_chara_str = json.load(f)
        global UnavailableChara
        for _id in unavailable_chara_str:
            UnavailableChara[int(_id)] = unavailable_chara_str[_id]

    # 保存数据
    def __save_pcr_data(self) -> None:
        with open(self.chara_name_path, 'w+', encoding='utf-8') as f:
            # noinspection PyTypeChecker
            json.dump(CHARA_NAME, f, indent=4, ensure_ascii=False)

    # 新增角色
    def add_chara(self, _id: int, names: list) -> None:
        CHARA_NAME[_id] = names
        self.__save_pcr_data()

    # 新增别称
    def add_nickname(self, _id: int, nickname: str) -> None:
        CHARA_NAME[_id].append(nickname)
        self.__save_pcr_data()


# 启动时加载一下
chara_master = CharaMaster()
# 各种基本图片资源加载一下
gadget_equip = Image.open(os.path.join(gadget_path, 'equip.png'))
gadget_star = Image.open(os.path.join(gadget_path, 'star.png'))
gadget_star_dis = Image.open(os.path.join(gadget_path, 'star_disabled.png'))
gadget_star_pink = Image.open(os.path.join(gadget_path, 'star_pink.png'))
unknown_chara_icon = Image.open(os.path.join(unit_path, f'icon_unit_{UNKNOWN}31.png.png'))
