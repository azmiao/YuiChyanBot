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
# 限制并发翻译数量，避免多个大图同时处理拖慢事件循环
_manga_semaphore = asyncio.Semaphore(2)
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
            open_timeout=10,
            close_timeout=5,
            ping_interval=20,
            ping_timeout=20
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


# 异步上传图片 | 返回任务ID
async def _upload_image(ev: CQEvent, img_path: str, img_name: str, mime_type: str) -> str:
    upload_url = 'https://api.cotrans.touhou.ai/task/upload/v1'
    data: dict[str, tuple[str | None, str | bytes | None, str | None]] = {
        'mime': (None, mime_type, None),
        'target_language': (None, 'CHS', None),
        'detector': (None, 'ctd', None),
        'direction': (None, 'default', None),
        'translator': (None, 'offline', None),
        'size': (None, 'X', None)
    }
    # 同步读取文件放到线程池，避免阻塞事件循环
    file_bytes = await asyncio.to_thread(_read_file, img_path)
    data['file'] = (img_name, file_bytes, mime_type)
    async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(10, read=20)) as async_session:
        upload_resp = await async_session.put(upload_url, files=data, headers=header)
    try:
        return upload_resp.json()['id']
    except (KeyError, ValueError):
        raise FunctionException(ev, f'上传图片失败，原始返回数据：{upload_resp.text}')


def _read_file(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


# 异步下载蒙版
async def _download_mask(ev: CQEvent, mask_url: str, mask_path: str) -> None:
    async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(10, read=15)) as session:
        async with session.stream('GET', mask_url, headers=header) as resp:
            resp.raise_for_status()
            content = await resp.aread()
    await asyncio.to_thread(_write_file, mask_path, content)


def _write_file(path: str, content: bytes) -> None:
    with open(path, 'wb') as f:
        f.write(content)


# 生成结果图片 | 图片处理较重，放到线程池执行
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
    # 限制同时翻译的数量，避免图片处理占满事件循环
    async with _manga_semaphore:
        try:
            # 上传图片并等待翻译完成
            id_ = await _upload_image(ev, img_path, img_name, mime_type)
            logger.info(f'> 漫画翻译：当前漫画ID为 [{id_}]')
            wss_url = f'wss://api.cotrans.touhou.ai/task/{id_}/event/v1'
            mask_url = await receive_wss(ev, wss_url, 120)

            # 下载蒙版
            logger.info(f'> 漫画翻译：蒙板URL为 [{mask_url}]')
            await _download_mask(ev, mask_url, mask_path)

            # 开始合成全新图片
            message = await asyncio.to_thread(create_image, img_path, mask_path)
            return message
        finally:
            # 无论成功失败都清理临时图片
            await asyncio.to_thread(_safe_unlink, img_path, mask_path)


def _safe_unlink(*paths: str) -> None:
    for path in paths:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
