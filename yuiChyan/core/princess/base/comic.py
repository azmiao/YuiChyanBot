import os.path
import re
from urllib.parse import urlparse, parse_qs

from aiocqhttp import MessageSegment
from httpx import AsyncClient

from yuiChyan import FunctionException
from yuiChyan.http_request import get_session_or_create, close_async_session
from ..util import *

sv_comic = Service('pcr-comic', use_exclude=False)


# 图片名称
def get_pic_name(id_):
    pre = 'episode_'
    end = '.png'
    return f'{pre}{id_}{end}'


# 下载
async def download_comic(session: AsyncClient, id_: str):
    base = 'https://comic.priconne-redive.jp/api/detail/'
    with open(os.path.join(comic_path, 'index.json'), encoding='utf8') as f:
        index = json.load(f)

    url = base + id_
    resp = await session.get(url)
    if 200 != resp.status_code:
        sv_comic.logger.error(f'PCR官方漫画: 详细信息获取失败，URL={url}')
        return
    data = resp.json()
    data = data[0]

    episode = data['episode_num']
    title = data['title']
    link = data['cartoon']
    index[episode] = {'title': title, 'link': link}

    sv_comic.logger.info(f'PCR官方漫画: 图片URL={link}')
    async with session.stream('GET', link) as resp:
        if 200 != resp.status_code:
            sv_comic.logger.error(f'PCR官方漫画: 图片下载失败，{resp.text}')
            return
        if re.search(r'image', resp.headers['content-type'], re.I):
            pic_name = get_pic_name(episode)
            save_path = os.path.join(comic_path, pic_name)
            with open(save_path, 'wb') as f:
                f.write(await resp.aread())
            sv_comic.logger.info(f'PCR官方漫画: 图片 [{pic_name}] 已保存')

    # 保存官漫目录信息
    with open(os.path.join(comic_path, 'index.json'), 'w', encoding='utf8') as f:
        # noinspection PyTypeChecker
        json.dump(index, f, ensure_ascii=False)


@sv_comic.on_prefix('PCR官漫')
async def comic(bot, ev):
    episode = str(ev.message).strip()
    if not re.fullmatch(r'\d{0,4}', episode):
        return
    episode = episode.lstrip('0')
    if not episode:
        raise FunctionException(ev, '命令错误，示例：官漫100')

    with open(os.path.join(comic_path, 'index.json'), encoding='utf8') as f:
        index = json.load(f)

    if episode not in index:
        raise FunctionException(ev, f'未查找到第{episode}话，敬请期待官方更新')
    title = index[episode]['title']

    pic_name = get_pic_name(episode)
    pic_path = os.path.abspath(os.path.join(comic_path, pic_name))
    image = MessageSegment.image(f'file:///{pic_path}')
    msg = f'PCR官漫第{episode}话 {title}\n{image}'
    await bot.send(ev, msg)


# 定时任务
@sv_comic.scheduled_job(minute='*/30', second='15')
async def update_manga():
    session: AsyncClient = get_session_or_create('PcrComic', True)
    # 获取最新漫画信息
    try:
        resp = await session.get(
            'https://comic.priconne-redive.jp/api/index',
            timeout=15
        )
    except:
        sv_comic.logger.info(f'PCR官方漫画: 网站连接失败，将于下次定时任务尝试')
        return
    data = resp.json()
    id_ = data['latest_cartoon']['id']
    episode = data['latest_cartoon']['episode_num']
    title = data['latest_cartoon']['title']

    with open(os.path.join(comic_path, 'index.json'), encoding='utf8') as f:
        index = json.load(f)

    # 检查是否已在目录中
    # 同一episode可能会被更新为另一张图片（官方修正），此时episode不变而id改变
    # 所以需要两步判断
    if episode in index:
        qs = urlparse(index.get(episode, {}).get('link', '')).query
        old_id = parse_qs(qs)['id'][0]
        if id_ == old_id:
            sv_comic.logger.info(f'PCR官方漫画: 未检测到更新')
            return

    # 确定已有更新，下载图片
    sv_comic.logger.info(f'PCR官方漫画: 发现更新 [{id_}]')
    await download_comic(session, id_)

    # 关闭会话
    await close_async_session('PcrComic', session)

    # 推送至各个订阅群
    pic_name = get_pic_name(episode)
    pic_path = os.path.abspath(os.path.join(comic_path, pic_name))
    image = MessageSegment.image(f'file:///{pic_path}')
    msg = f'检测到PCR官方漫画更新！\n第{episode}话 {title}\n{image}'
    await sv_comic.broadcast(msg, 'PCR官方漫画', 1)
