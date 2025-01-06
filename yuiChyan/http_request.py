from typing import Dict

import httpx
from httpx import AsyncClient, Client

from yuiChyan.exception import *

# 高性能http请求工具session会话统一缓存
session_map: Dict[str, Client] = {}
async_session_map: Dict[str, AsyncClient] = {}


# 获取缓存的session | if_async: 是否是异步的session | create_if_none: 是否要在不存在的时候创建
def get_session_or_create(name: str, if_async: bool = False, proxy: Optional[str] = None,
                          create_if_none: bool = True) -> Client | AsyncClient:
    _session_map = async_session_map if if_async else session_map
    create_session_func = create_async_session if if_async else create_session
    session_type = "AsyncClient" if if_async else "Client"

    session = _session_map.get(name)
    if session:
        return session
    if create_if_none:
        return create_session_func(name, True, proxy)

    raise SessionNotFoundException(f'找不到 {session_type} [{name}]')


# 手动关闭同步会话
def close_session(name: str, session: Client):
    if isinstance(session, Client):
        session.close()
        session_map.pop(name)
    else:
        pass


# 手动关闭异步会话
async def close_async_session(name: str, session: AsyncClient):
    if isinstance(session, AsyncClient):
        await session.aclose()
        async_session_map.pop(name)
    else:
        pass


# 保存session至缓存
def save_session(name: str, session: Client | AsyncClient):
    if isinstance(session, Client):
        session_map[name] = session
    elif isinstance(session, AsyncClient):
        async_session_map[name] = session
    else:
        raise SessionNotFoundException('不支持的 Session 类型，只支持 [Session] 和 [ClientSession]')


# 创建同步session | is_save: 是要保存至缓存 还是 一次性
def create_session(name: str, is_save: bool = False, proxy: Optional[str] = None) -> Client:
    if name in session_map or name in async_session_map:
        raise SessionExistException(f'Session [{name}] 已经存在')
    session = httpx.Client(proxy=proxy, verify=False, timeout=httpx.Timeout(10, read=15))
    if is_save:
        save_session(name, session)
    return session


# 创建异步session | is_save: 是要保存至缓存 还是 一次性
def create_async_session(name: str, is_save: bool = False, proxy: Optional[str] = None) -> AsyncClient:
    if name in session_map or name in async_session_map:
        raise SessionExistException(f'AsyncSession [{name}] 已经存在')
    async_session = httpx.AsyncClient(proxy=proxy, verify=False, timeout=httpx.Timeout(10, read=15))
    if is_save:
        save_session(name, async_session)
    return async_session
