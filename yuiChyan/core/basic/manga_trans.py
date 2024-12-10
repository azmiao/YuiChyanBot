import base64
import json
import mimetypes
import os
import re
from io import BytesIO
from urllib import request

import requests
import websockets
from PIL import Image
from aiocqhttp import MessageSegment

from yuiChyan import FunctionException
from yuiChyan.core.xqa import extract_file
from yuiChyan.resources import base_img_path
from yuiChyan.util import FreqLimiter

manga_path = os.path.join(base_img_path, 'manga')
os.makedirs(manga_path, exist_ok=True)


# 解析并保存
async def parse_and_save_image(bot, ev, str_raw: str) -> str:
    # 找出第一个CQ码
    cq_code = re.search(r'(\[CQ:iamge,(\S+?)])', str_raw)
    if not cq_code:
        raise FunctionException(ev, f'无法从消息中获取图片，请检查')
    is_base64, image_file, image_file_name, image_url = await extract_file(cq_code[1])
    # 保存
    return await save_image(bot, ev, image_file_name, image_file, image_url)


# 保存图片
async def save_image(bot, ev, img_name: str, img_file: str, img_url: str) -> str:
    file = os.path.join(manga_path, img_name)
    # 如果没有image_url，说明是GO-CQ的客户端，重新取一下图片URL
    if not img_url:
        try:
            img_data = await bot.get_image(file=img_file)
        except Exception as e:
            raise FunctionException(ev, f'调用get_image接口查询图片{img_file}出错:{str(e)}')
        img_url = img_data['url']

    # 开始下载图片
    try:
        if not os.path.isfile(file):
            request.urlretrieve(url=img_url, filename=file)
    except Exception as e:
        raise FunctionException(ev, f'从{img_url}下载图片{img_name}出错:{str(e)}')
    return img_name


# 接收WS数据
async def receive_wss(wss_url: str, timeout: int) -> str:
    mask_url = ''
    lmt = FreqLimiter(timeout)
    lmt.start_cd(wss_url)
    async with websockets.connect(wss_url) as ws:
        while True:
            if lmt.check(wss_url):
                return mask_url
            recv = await ws.recv()
            json_dump = json.loads(recv)
            result = json_dump.get('result', {})
            if result:
                mask_url = result.get('translation_mask', '')
                break
    return mask_url


# 生成结果图片
async def create_image(img_path: str, mask_path: str) -> MessageSegment:
    old_image = Image.open(img_path).convert("RGBA")
    mask = Image.open(mask_path).convert("RGBA")
    old_image.paste(im=mask, mask=mask)
    buf = BytesIO()
    old_image.save(buf, format='PNG')
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return MessageSegment.image(base64_str)


# 漫画翻译
async def manga_tran(img_name: str) -> MessageSegment:
    img_path = os.path.join(manga_path, img_name)
    mask_path = os.path.join(manga_path, f'MASK_{img_name}.png')
    mime_type, _ = mimetypes.guess_type(img_name)
    upload_url = 'https://api.cotrans.touhou.ai/task/upload/v1'
    header = {
        'Origin': 'https://cotrans.touhou.ai',
        'Referer': 'https://cotrans.touhou.ai',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}
    data = {
        'mime': (None, mime_type, None),
        'target_language': (None, 'CHS', None),
        'detector': (None, 'default', None),
        'direction': (None, 'default', None),
        'translator': (None, 'youdao', None),
        'size': (None, 'L', None)
    }
    with open(img_path, 'rb') as f:
        data['file'] = (img_name, f.read(), mime_type)
    # 上传图片
    upload_resp = requests.put(upload_url, files=data, headers=header)
    # 等待翻译完成
    id_ = upload_resp.json()['id']
    wss_url = f'wss://api.cotrans.touhou.ai/task/{id_}/event/v1'
    mask_url = await receive_wss(wss_url, 60)
    # 保存蒙板
    request.urlretrieve(url=mask_url, filename=mask_path)
    # 开始合成全新图片
    return await create_image(img_path, mask_path)
