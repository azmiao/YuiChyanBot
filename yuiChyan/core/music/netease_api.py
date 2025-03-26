import time

from httpx import AsyncClient

from .utils import save_music_temp
from yuiChyan.http_request import get_session_or_create


class NetEase:
    def __init__(self):
        self.header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) '
            + 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 '
            + 'Safari/537.36',
            'X-Real-IP': '39.156.69.79',
            'X-Forwarded-For': '39.156.69.79',
        }
        self.cookies = {
            'appver': '1.5.2'
        }

    async def search(self, keyword: str, stype: int = 1, offset: int = 0, total: str = 'true') -> dict:
        async_session: AsyncClient = get_session_or_create('NetEaseMusic', True)
        base_url = 'http://music.163.com/api/search/get/web'
        data = {
            's': keyword,
            'type': stype,
            'offset': offset,
            'total': total,
            'limit': 60
        }
        resp = await async_session.post(
            base_url,
            data=data,
            headers=self.header,
            timeout=3
        )
        return resp.json()


# 查询接口
async def search_api(group_id: int, user_id: int, keyword: str, result_num: int = 5) -> str:
    song_list = []
    time_time = time.time()
    # 查询
    data = await NetEase().search(keyword)
    if data and data['code'] == 200:
        for item in data['result']['songs'][:result_num]:
            song_list.append(
                {
                    'name': item['name'],
                    'id': item['id'],
                    'artists': ' '.join(
                        [artist['name'] for artist in item['artists']]
                    ),
                    'type': '163',
                    'time': time_time
                }
            )

    # 保存至缓存
    await save_music_temp(group_id, user_id, song_list)

    # 整理
    if not song_list:
        msg = '没有找到任何歌曲哦~'
    else:
        msg = '> 查询到相关歌曲：'
        for idx, song in enumerate(song_list):
            msg += f'\n{idx}. {song["name"]} - {song["artists"]}'
        msg += f'\n> 请在30秒内发送形如"点歌 1"的命令来听歌吧，仅限搜歌人操作'
    return msg
