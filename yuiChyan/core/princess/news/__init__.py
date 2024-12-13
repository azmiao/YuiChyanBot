

from yuiChyan.service import Service
from .spider import *

sv_tw = Service('pcr-news-tw')
sv_bl = Service('pcr-news-bili')
sv_jp = Service('pcr-news-jp')


@sv_tw.on_match('PCR台服新闻')
async def send_sonet_news(bot, ev):
    msg = await create_news(SonetSpider)
    await bot.send(ev, msg, at_sender=True)


@sv_bl.on_match('PCR国服新闻')
async def send_bili_news(bot, ev):
    msg = await create_news(BiliSpider)
    await bot.send(ev, msg, at_sender=True)


@sv_jp.on_match('PCR日服新闻')
async def send_jp_news(bot, ev):
    msg = await create_news(JpSpider)
    await bot.send(ev, msg, at_sender=True)


# @sv_tw.scheduled_job(minute='*/5')
async def sonet_news_poller():
    try:
        await news_poller(SonetSpider, sv_tw, '台服官网')
    except Exception:
        sv_tw.logger.info(f'PCR台服官网连接失败')


# @sv_bl.scheduled_job(minute='*/5')
async def bili_news_poller():
    try:
        await news_poller(BiliSpider, sv_bl, '国服官网')
    except Exception:
        sv_bl.logger.info(f'PCR国服官网连接失败')


# @sv_jp.scheduled_job(minute='*/5')
async def jp_news_poller():
    try:
        await news_poller(JpSpider, sv_jp, '日服官网')
    except Exception:
        sv_bl.logger.info(f'PCR日服官网连接失败')


async def create_news(_spider, max_num=5):
    try:
        if not _spider.item_cache:
            await _spider.get_update()
        news = _spider.item_cache
        news = news[:min(max_num, len(news))]
        msg = _spider.format_items(news)
    except Exception:
        msg = f'官网连接失败'
    return msg


async def news_poller(_spider, sv: Service, TAG):
    if not _spider.item_cache:
        await _spider.get_update()
        sv.logger.info(f'{TAG}新闻缓存为空，已加载至最新')
        return
    news = await _spider.get_update()
    if not news:
        sv.logger.info(f'未检索到{TAG}新闻更新')
        return
    sv.logger.info(f'检索到{len(news)}条{TAG}新闻更新！')
    await sv.broadcast(_spider.format_items(news), TAG, interval_time=0.5)
