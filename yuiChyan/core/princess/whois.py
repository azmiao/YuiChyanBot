
from yuiChyan.util import FreqLimiter
from .chara import get_chara_by_id
from .chara_manager import chara_manager
from .util import *

lmt = FreqLimiter(5)


@sv.on_prefix('PCR谁是')
async def whois(bot, ev):
    name = str(ev.message).strip()
    if not name:
        return
    id_ = chara_manager.roster.get_id(name)

    # 如果找到了就直接返回
    if id_ != chara_manager.UNKNOWN_ID:
        chara = get_chara_by_id(id_)
        image = await chara.get_icon_image()
        msg = f'> {chara.name}\n{image}'
        await bot.send(ev, msg, at_sender=True)
        return

    # 找不到就猜测
    id_, guess_name, confi = chara_manager.roster.guess_id(name)
    chara = get_chara_by_id(id_)
    image = await chara.get_icon_image()
    
    if confi < 60:
        msg = f'> PCR似乎没有和 [{name}] 名字相近的人'
    else:
        msg = f'> PCR似乎没有叫 [{name}] 的人，您有 {confi}% 的可能在找{guess_name}:\n{image}'
    await bot.send(ev, msg)
