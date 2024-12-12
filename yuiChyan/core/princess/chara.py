import asyncio
import os
from io import BytesIO

from PIL import Image
from PIL.Image import Resampling
from curl_cffi.requests import AsyncSession

from yuiChyan.exception import FunctionException
from yuiChyan.http_request import get_session_or_create, close_session
from .chara_manager import chara_manager, gadget_star, gadget_star_dis, gadget_star_pink, gadget_equip, is_npc
from .util import unit_path, sv


class Chara:

    def __init__(self, id_: int, star: int = 0, equip: int = 0, second_equip: int = 0):
        self.id: int = id_  # 角色ID
        self.star: int = star  # 星级
        self.equip: int = equip  # 专武1
        self.second_equip: int = second_equip  # 专武2
        self.name: str = chara_manager.CHARA_NAME.get(self.id, chara_manager.UNKNOWN_NAME)[0]  # 角色名

    # 获取图片路径
    async def get_icon_path(self, star: int = 0) -> str:
        star = star or self.star
        # 选择一个星级区段
        star = 1 if 1 <= star < 3 else 3 if 3 <= star < 6 else 6
        # 构建检查顺序的文件路径
        res_paths = [
            os.path.join(unit_path, f'icon_unit_{self.id}{star}1.png'),
            os.path.join(unit_path, f'icon_unit_{self.id}31.png'),
            os.path.join(unit_path, f'icon_unit_{self.id}11.png')
        ]
        # 依次检查文件是否存在，若存在则返回路径
        for path in res_paths:
            if os.path.exists(path):
                return path

        session: AsyncSession = get_session_or_create('PcrUnit', True)
        # 文件均不存在，则下载资源
        await asyncio.gather(
            download_chara_icon(session, self.id, 6),
            download_chara_icon(session, self.id, 3),
            download_chara_icon(session, self.id, 1),
        )
        # 关闭会话
        close_session('PcrUnit', session)

        # 在下载之后，依次重新检查文件是否存在
        for path in res_paths:
            if os.path.exists(path):
                return path
        # 若下载后依然不存在，则返回未知角色图标
        return os.path.join(unit_path, f'icon_unit_{chara_manager.UNKNOWN_ID}31.png')

    # 生成图标
    async def render_icon(self, size: int, star_slot_verbose: bool = True) -> Image:
        icon_path = await self.get_icon_path()
        pic = Image.open(icon_path).convert('RGBA').resize((size, size), Resampling.LANCZOS)

        l: int = size // 6
        star_lap: int = round(l * 0.15)
        margin_x: int = (size - 6 * l) // 2
        margin_y: int = round(size * 0.05)
        if self.star:
            for i in range(5 if star_slot_verbose else min(self.star, 5)):
                a = i * (l - star_lap) + margin_x
                b = size - l - margin_y
                s = gadget_star if self.star > i else gadget_star_dis
                s = s.resize((l, l), Resampling.LANCZOS)
                pic.paste(s, (a, b, a + l, b + l), s)
            if 6 == self.star:
                a = 5 * (l - star_lap) + margin_x
                b = size - l - margin_y
                s = gadget_star_pink
                s = s.resize((l, l), Resampling.LANCZOS)
                pic.paste(s, (a, b, a + l, b + l), s)
        if self.equip:
            l: int = round(l * 1.5)
            a = margin_x
            b = margin_x
            s = gadget_equip.resize((l, l), Resampling.LANCZOS)
            pic.paste(s, (a, b, a + l, b + l), s)
        return pic


# 根据ID查询角色
def get_chara_by_id(id_: int, star: int = 0, equip: int = 0, second_equip: int = 0) -> Chara:
    return Chara(id_, star, equip, second_equip)


# 下载头像 | 返回值：0正常，1不存在，2失败，3出错
async def download_chara_icon(session: AsyncSession, id_: int, star: int) -> int:
    url = f'https://redive.estertion.win/icon/unit/{id_}{star}1.webp'
    save_path = os.path.join(unit_path, f'icon_unit_{id_}{star}1.png')
    sv.logger.info(f'> 开始下载PCR角色 [{id_}] URL={url}')
    try:
        rsp = await session.get(url, stream=True, timeout=5)
        if 200 == rsp.status_code:
            img = Image.open(BytesIO(await rsp.content))
            img.save(save_path)
            sv.logger.info(f'- 已保存至 [{save_path}]')
            return 0
        elif 404 == rsp.status_code:
            sv.logger.info(f'- 角色头像 [{id_}{star}1] 不存在，将跳过')
            return 1
        else:
            sv.logger.info(f'- 角色头像 [{id_}{star}1] 下载失败：CODE={rsp.status_code}')
            return 2
    except Exception as e:
        sv.logger.error(f'- 角色头像 [{id_}{star}1] 下载出错：{str(e)}')
        return 3


# 手动更新所有头像 | 只下载不存在的
@sv.on_command('更新所有PCR头像')
async def download_all_chara_icon(bot, ev):
    try:
        tasks = []
        session: AsyncSession = get_session_or_create('PcrUnitUpdate', True)
        for id_ in chara_manager.CHARA_NAME:
            if is_npc(id_):
                continue

            if not os.path.exists(os.path.join(unit_path, f'icon_unit_{id_}11.png')):
                tasks.append(download_chara_icon(session, id_, 1))

            if not os.path.exists(os.path.join(unit_path, f'icon_unit_{id_}31.png')):
                tasks.append(download_chara_icon(session, id_, 3))

            if not os.path.exists(os.path.join(unit_path, f'icon_unit_{id_}61.png')):
                tasks.append(download_chara_icon(session, id_, 6))

        ret = await asyncio.gather(*tasks)
        # 关闭会话
        close_session('PcrUnitUpdate', session)

        success = sum(r == 0 for r in ret)
        await bot.send(ev, f'> PCR头像更新完成! \n下载成功 {success}/{len(ret)} 个头像')
    except Exception as e:
        raise FunctionException(ev, f'> PCR头像更新出错: {type(e)}，{str(e)}')
