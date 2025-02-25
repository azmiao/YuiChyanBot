import re
from enum import IntEnum, unique

from aiocqhttp import Event as CQEvent

from .arena import sv
from .old_main import _QueryArenaImageAsync, _QueryArenaTextAsync, _update_dic_cron


@unique
class RegionEnum(IntEnum):
    All = 1
    Bilibili = 2
    Taiwan = 3
    Japan = 4


@sv.on_rex(r'([bB台日]?)怎么[拆解](.+)')
async def query_arena(bot, ev):
    # # (b|B|台|日) | 阵容
    que_type, str_raw = ev['match'].group(1), ev['match'].group(2)
    match str(que_type):
        case '台':
            region = RegionEnum.Taiwan
        case '日':
            region = RegionEnum.Japan
        case '':
            region = RegionEnum.All
        case _:
            region = RegionEnum.Bilibili
    await parse_and_query(bot, ev, region, str(str_raw).strip())


# 解析图片或者文字阵容
async def parse_and_query(bot, ev: CQEvent, region: RegionEnum, str_raw: str):
    cq_code = re.match(r'(\[CQ:image,(\S+?)])', str_raw)
    if not cq_code:
        # 不是图片 | 解析阵容
        await _QueryArenaTextAsync(str_raw, int(region), bot, ev)
    else:
        # 是图片 | 解析图片并查询
        await _QueryArenaImageAsync(str_raw, int(region), bot, ev)


# 更新字典图标缓存
@sv.scheduled_job(hour='3', minute='21')
async def update_dic_cron():
    await _update_dic_cron()
