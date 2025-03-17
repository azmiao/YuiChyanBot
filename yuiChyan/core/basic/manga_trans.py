import asyncio
import json
import mimetypes
import os
from asyncio import timeout

import httpx
import websockets
from PIL import Image
from aiocqhttp import MessageSegment

from yuiChyan import logger, CQEvent, FunctionException
from yuiChyan.resources import base_img_path
from yuiChyan.util import pic2b64
from yuiChyan.util.parse import parse_single_image, save_image

manga_path = os.path.join(base_img_path, 'manga')
os.makedirs(manga_path, exist_ok=True)
header = {
    'Origin': 'https://cotrans.touhou.ai',
    'Referer': 'https://cotrans.touhou.ai',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
}

# 解析并保存
async def parse_and_save_image(ev, str_raw: str) -> str:
    image_file, image_file_name, image_url = await parse_single_image(ev, str_raw)
    image_file_name = image_file_name.replace('.image', '.png')
    image_path = os.path.join(manga_path, image_file_name)
    # 保存
    return await save_image(ev, image_file, image_file_name, image_url, image_path)


# 接收WS数据
async def receive_wss(ev: CQEvent, wss_url: str, _timeout: int) -> str:
    async with websockets.connect(
            wss_url,
            additional_headers=header,
            max_size=2 ** 20 * 10,
            open_timeout=10
    ) as ws:
        try:
            async with timeout(_timeout):
                return await _receive_data(ws)
        except asyncio.TimeoutError:
            raise FunctionException(ev, 'WS获取漫画蒙版超时')


# 解耦数据接收逻辑
async def _receive_data(ws) -> str:
    while True:
        recv = await ws.recv()
        json_dump = json.loads(recv)
        if result := json_dump.get('result', {}):
            if mask_url := result.get('translation_mask', ''):
                return mask_url


# 生成结果图片
def create_image(img_path: str, mask_path: str) -> MessageSegment:
    old_image = Image.open(img_path).convert("RGBA")
    mask = Image.open(mask_path).convert("RGBA")
    old_image.paste(im=mask, mask=mask)
    b_ = pic2b64(old_image)
    return MessageSegment.image(b_)


# 漫画翻译
async def manga_tran(ev: CQEvent, img_name: str) -> MessageSegment:
    img_path = os.path.join(manga_path, img_name)
    mask_path = os.path.join(manga_path, f'MASK_{img_name}.png')
    mime_type, _ = mimetypes.guess_type(img_name)
    upload_url = 'https://api.cotrans.touhou.ai/task/upload/v1'
    data = {
        'mime': (None, mime_type, None),
        'target_language': (None, 'CHS', None),
        'detector': (None, 'default', None),
        'direction': (None, 'default', None),
        'translator': (None, 'offline', None),
        'size': (None, 'L', None)
    }
    with open(img_path, 'rb') as f:
        data['file'] = (img_name, f.read(), mime_type)
    # 异步上传图片
    async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(10, read=15)) as async_session:
        upload_resp = await async_session.put(upload_url, files=data, headers=header)
    # 等待翻译完成
    try:
        id_ = upload_resp.json()['id']
    except:
        raise FunctionException(ev, f'上传图片失败，原始返回数据：{upload_resp.json()}')

    # 异步WS获取蒙版URL
    logger.info(f'> 漫画翻译：当前漫画ID为 [{id_}]')
    wss_url = f'wss://api.cotrans.touhou.ai/task/{id_}/event/v1'
    mask_url = await receive_wss(ev, wss_url, 60)

    # 同步保存蒙板
    logger.info(f'> 漫画翻译：蒙板URL为 [{mask_url}]')
    with httpx.Client(verify=False, timeout=httpx.Timeout(10, read=15)) as session:
        with session.stream('GET', mask_url, headers=header) as resp:
            with open(mask_path, 'wb') as f:
                f.write(resp.read())

    # 开始合成全新图片
    message = create_image(img_path, mask_path)
    # 删除不需要的图片资源
    os.unlink(img_path)
    os.unlink(mask_path)
    return message
