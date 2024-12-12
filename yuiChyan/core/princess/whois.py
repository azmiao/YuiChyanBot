
from yuiChyan.util import FreqLimiter
from .chara import roster, get_chara_by_id
from .chara_manager import UNKNOWN
from .util import *

lmt = FreqLimiter(5)


@sv.on_prefix('PCR谁是')
async def whois(bot, ev):
    name = str(ev.message).strip()
    if not name:
        return
    id_ = roster.get_id(name)
    confi = 100
    guess = False
    if id_ == UNKNOWN:
        id_, guess_name, confi = roster.guess_id(name)
        guess = True
    c = get_chara_by_id(id_)
    
    if confi < 60:
        msg = f'兰德索尔似乎没有和"{name}"名字相近的人欸'
        await bot.send(ev, msg)
        return

    if guess:
        msg = f'兰德索尔似乎没有叫"{name}"的人欸，您有{confi}%的可能在找{guess_name} {c.icon.cqcode} {c.name}'
        await bot.send(ev, msg)
    else:
        msg = f'{c.icon.cqcode} {c.name}'
        await bot.send(ev, msg, at_sender=True)
