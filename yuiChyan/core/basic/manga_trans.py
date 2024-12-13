import base64
import json
import mimetypes
import os
from io import BytesIO
from urllib import request

import requests
import websockets
from PIL import Image
from aiocqhttp import MessageSegment

from yuiChyan.resources import base_img_path
from yuiChyan.util import FreqLimiter
from yuiChyan.util.parse import parse_single_image, save_image

manga_path = os.path.join(base_img_path, 'manga')
os.makedirs(manga_path, exist_ok=True)


# 解析并保存
async def parse_and_save_image(ev, str_raw: str) -> str:
    image_file, image_file_name, image_url = await parse_single_image(ev, str_raw)
    image_path = os.path.join(manga_path, image_file_name)
    # 保存
    return await save_image(ev, image_file, image_file_name, image_url, image_path)


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
