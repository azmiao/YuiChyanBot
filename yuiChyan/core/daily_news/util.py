import datetime
import os

import httpx

from yuiChyan import base_img_path

daily_news_path = os.path.join(base_img_path, 'daily_news')
os.makedirs(daily_news_path, exist_ok=True)


# 查询早报的图片URL和时间
async def query_zb_data() -> dict:
    async with httpx.AsyncClient(verify=False) as session:
        zb_data = await session.get(
            'https://api.03c3.cn/api/zb?type=jsonImg',
            timeout=10,
            headers={'content-type': 'application/json'},
        )
    zb_json = dict(zb_data.json())
    return zb_json.get('data', {})


# 判断日期是否一致
async def judge_time(time_str: str) -> bool:
    if not time_str:
        return False
    now = datetime.datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')
    return time_str == formatted_date


# 下载图片
async def download_image(image_url: str):
    now = datetime.datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')
    save_path = os.path.join(daily_news_path, f'{formatted_date}.png')
    async with httpx.AsyncClient(verify=False) as session:
        async with session.stream('GET', image_url) as resp:
            with open(save_path, 'wb') as f:
                f.write(await resp.aread())


# 同步清理旧的图片
def clean_old_images():
    if not os.path.exists(daily_news_path):
        return
    # 遍历目录中的所有文件
    for filename in os.listdir(daily_news_path):
        file_path = os.path.join(daily_news_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except:
            pass


# 获取今日图片
async def get_today_news_image():
    now = datetime.datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')
    image_path = os.path.join(daily_news_path, f'{formatted_date}.png')
    if os.path.isfile(image_path):
        return f'[CQ:image,file=file:///{image_path}]'
    else:
        return None
