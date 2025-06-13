from aiocqhttp import Event, MessageSegment

from yuiChyan import YuiChyan
from yuiChyan.service import Service
from .netease_api import search_api
from .utils import check_music_temp

sv = Service('music', help_cmd='音乐帮助')


@sv.on_prefix('搜歌')
async def search_music(bot: YuiChyan, ev: Event):
    music_name = str(ev.message).strip()
    if not music_name:
        return
    msg = await search_api(ev.group_id, ev.user_id, music_name)
    await bot.send(ev, msg, at_sender=True)


@sv.on_prefix('点歌')
async def select_music(bot: YuiChyan, ev: Event):
    music_id_str = str(ev.message).strip()
    if not music_id_str:
        return
    # 确保数字
    try:
        music_id = int(music_id_str)
    except:
        return
    # 确认缓存是否过期并返回音乐缓存列表
    song_list = await check_music_temp(ev.group_id, ev.user_id)
    if not song_list:
        msg = '\n您还没有搜过歌或命令已超时，请先使用命令"搜歌 歌名"来搜索'
        await bot.send(ev, msg, at_sender=True)
        return

    song = song_list[music_id]
    msg_ = MessageSegment(
        type_='music',
        data={
            'id': str(song['id']),
            'type': song['type'],
            'content': song['artists']
        }
    )
    await bot.send(ev, msg_)
