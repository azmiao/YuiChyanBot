from .util import *
from yuiChyan.util import FreqLimiter

lmt = FreqLimiter(5)


@sv.on_prefix('PCR谁是')
async def whois(bot, ev):
    name = escape(ev.message.extract_plain_text().strip())
    if not name:
        return
    id_ = chara.name2id(name)
    confi = 100
    guess = False
    if id_ == chara.UNKNOWN:
        id_, guess_name, confi = chara.guess_id(name)
        guess = True
    c = chara.fromid(id_)
    
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
