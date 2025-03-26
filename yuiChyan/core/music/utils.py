import time
from typing import Optional

music_temp = {}


# 保存至音乐缓存
async def save_music_temp(group_id: int, user_id: int, song_list: list[dict]):
    global music_temp
    group_dict = music_temp.get(str(group_id), {})
    group_dict[str(user_id)] = song_list
    music_temp[str(group_id)] = group_dict


# 确认缓存是否过期并返回音乐缓存列表
async def check_music_temp(group_id: int, user_id: int) -> Optional[list[dict]]:
    global music_temp
    group_dict = music_temp.get(str(group_id), {})
    song_list = group_dict.get(str(user_id), [])
    # 校验是否过期
    if song_list:
        first_song = song_list[0]
        time_stamp = first_song.get('time', 0.0)
        if time_stamp < time.time() - 30:
            return []
    return song_list
