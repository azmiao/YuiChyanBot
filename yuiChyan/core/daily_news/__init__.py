from yuiChyan import YuiChyan, CQEvent, FunctionException
from yuiChyan.service import Service
from .util import *

sv = Service('daily_news', help_cmd='今日早报帮助')


@sv.on_match('今日早报')
async def today_news(bot: YuiChyan, ev: CQEvent):
    image_msg = await get_today_news_image()
    if image_msg:
        await bot.send(ev, image_msg)
        return

    # 没有图片就需要检测一下
    zb_data = await query_zb_data()
    has_news = await judge_time(zb_data.get('datetime', ''))
    if not has_news:
        raise FunctionException(ev, f'今日早报还未出炉哦，请耐心等待~')

    # 清理一下旧的图片
    clean_old_images()
    # 今天早报有了就下载
    await download_image(zb_data.get('imageurl', ''))
    image_msg = await get_today_news_image()
    if not image_msg:
        image_msg = '今日早报获取失败，请检查！'
    await bot.send(ev, image_msg)
