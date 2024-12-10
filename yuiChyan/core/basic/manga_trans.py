import json
import os

import websockets

from yuiChyan.http_request import get_session_or_create
from yuiChyan.util import FreqLimiter


async def receive_wss(wss_url: str, timeout: int) -> str:
    mask_url = ''
    lmt = FreqLimiter(timeout)
    lmt.start_cd(wss_url)
    async with websockets.connect(wss_url) as ws:
        while True:
            if lmt.check(wss_url):
                return mask_url
            recv = ws.recv()
            json_dump = json.loads(str(recv))
            result = json_dump.get('result', {})
            if result:
                mask_url = result.get('translation_mask', '')
                break
    return mask_url


async def manga_tran():
    session = get_session_or_create('Manga')
    img_path = os.path.join(os.path.dirname(__file__), '03D3AFB5D2D1887DEB3032FA18E8E452.png')
    upload_url = 'https://api.cotrans.touhou.ai/task/upload/v1'
    header = {
        'Origin': 'https://cotrans.touhou.ai',
        'Referer': 'https://cotrans.touhou.ai',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}
    data = {
        'mime': (None, 'image/png', None),
        'target_language': (None, 'CHS', None),
        'detector': (None, 'default', None),
        'direction': (None, 'default', None),
        'translator': (None, 'youdao', None),
        'size': (None, 'L', None)
    }
    with open(img_path, 'rb') as f:
        data['file'] = ('03D3AFB5D2D1887DEB3032FA18E8E452.png', f.read(), 'image/png')
    upload_resp = session.put(upload_url, files=data, headers=header)

    id_ = upload_resp.json()['id']
    wss_url = f'wss://api.cotrans.touhou.ai/task/{id_}/event/v1'
    mask_url = await receive_wss(wss_url, 60)
    print(mask_url)
