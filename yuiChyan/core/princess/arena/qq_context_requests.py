from enum import IntEnum, unique
from typing import Dict, Optional
from datetime import datetime


@unique
class RegionEnum(IntEnum):
    Unknown = 1
    Bilibili = 1 << 1
    Taiwan = 1 << 2
    Japan = 1 << 3
    All = 1 << 4


class QueryRequestContext:
    def __init__(self, region: RegionEnum = RegionEnum.Unknown):
        self.time = datetime.now()
        self.region = region


gs_qq_id2request: Dict[int, QueryRequestContext] = {}
gs_seconds_to_wait = 60
_gs_last_clean_time = datetime.now()


def _ClearOldRequests():
    current_time = datetime.now()
    if (current_time - _gs_last_clean_time).seconds < 599:
        return
    to_delete = [qq_id for qq_id, context in gs_qq_id2request.items()
                 if (current_time - context.time).seconds >= gs_seconds_to_wait]
    for qq_id in to_delete:
        gs_qq_id2request.pop(qq_id, None)


def GetRequest(qq_id: int) -> Optional[QueryRequestContext]:
    _ClearOldRequests()

    if qq_id not in gs_qq_id2request:
        return None
    req = gs_qq_id2request[qq_id]
    if (datetime.now() - req.time).seconds >= gs_seconds_to_wait:
        return None
    return req


def PopRequest(qq_id: int) -> Optional[QueryRequestContext]:
    req = GetRequest(qq_id)
    gs_qq_id2request.pop(qq_id, None)
    return req
