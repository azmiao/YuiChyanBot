import random

from nonebot import on_command

from hoshino import R, service, priv, util


# basic function for debug, not included in Service('chat')
@on_command('zai?', aliases=('在?', '在？', '在吗', '在么？', '在嘛', '在嘛？'), only_to_me=True)
async def say_hello(session):
    await session.send('优衣酱在的哟~')


sv = Service('chat', visible=False)

@sv.on_match('沙雕机器人')
async def say_sorry(bot, ev):
    await bot.send(ev, '喵喵喵？')


@sv.on_match(('老婆', 'waifu', 'laopo'), only_to_me=True)
async def chat_waifu(bot, ev):
    if not priv.check_permission(ev, priv.SUPERUSER):
        await bot.send(ev, R.img('laopo.jpg').cqcode)
    else:
        await bot.send(ev, 'mua~')


@sv.on_match('老公', only_to_me=True)
async def chat_laogong(bot, ev):
    await bot.send(ev, '你给我滚！', at_sender=True)


@sv.on_match('mua', only_to_me=True)
async def chat_mua(bot, ev):
    await bot.send(ev, '笨蛋~', at_sender=True)


@sv.on_match(('我有个朋友说他好了', '我朋友说他好了',))
async def ddhaole(bot, ev):
    await bot.send(ev, '那个朋友是不是你弟弟？')


@sv.on_match('我好了')
async def nihaole(bot, ev):
    await bot.send(ev, '不许好，憋回去！')