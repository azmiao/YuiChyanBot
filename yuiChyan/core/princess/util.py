import os

from yuiChyan.service import Service
from yuiChyan.resources import base_img_path

# 当前路径
current_dir = os.path.dirname(__file__)
# 基础资源路径
gadget_path = os.path.join(current_dir, 'gadget')
# 角色别称路径
chara_name_path = os.path.join(current_dir, 'CHARA_NAME.json')
# 不可用角色路径
unavailable_chara_path = os.path.join(current_dir, 'UnavailableChara.json')

# PCR图片路径
base_pcr_path = os.path.join(base_img_path, 'pcr')
os.makedirs(base_pcr_path, exist_ok=True)
# 头像路径
unit_path = os.path.join(base_pcr_path, 'unit')
os.makedirs(unit_path, exist_ok=True)
# 漫画路径
comic_path = os.path.join(base_pcr_path, 'comic')
os.makedirs(comic_path, exist_ok=True)

sv = Service('pcr')
