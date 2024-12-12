from typing import Dict, Union

from curl_cffi import requests
from curl_cffi.requests import AsyncSession, Session

from yuiChyan.exception import *

# 高性能http请求工具session会话统一缓存
session_map: Dict[str, Session] = {}
async_session_map: Dict[str, AsyncSession] = {}


# 获取缓存的session | if_async: 是否是异步的session | create_if_none: 是否要在不存在的时候创建
def get_session_or_create(name: str, if_async: bool = False, create_if_none: bool = True) -> Session | AsyncSession:
    _session_map = async_session_map if if_async else session_map
    create_session_func = create_async_session if if_async else create_session
    session_type = "AsyncSession" if if_async else "Session"

    session = _session_map.get(name)
    if session:
        return session
    if create_if_none:
        return create_session_func(name, True)

    raise SessionNotFoundException(f'找不到 {session_type} [{name}]')


# 一个调度器函数，决定使用哪个关闭函数
def close_session(name: str, session: Union[Session, AsyncSession, None]):
    # 为空就直接跳过
    if not session:
        return

    if isinstance(session, Session):
        _close_sync_session(name, session)
    elif isinstance(session, AsyncSession):
        # 使用事件循环运行异步关闭
        import asyncio
        asyncio.run(_close_async_session(name, session))
    else:
        pass


# 保存session至缓存
def save_session(name: str, session: Session | AsyncSession):
    if isinstance(session, Session):
        session_map[name] = session
    elif isinstance(session, AsyncSession):
        async_session_map[name] = session
    else:
        raise SessionNotFoundException('不支持的 Session 类型，只支持 [Session] 和 [AsyncSession]')


# 创建同步session | is_save: 是要保存至缓存 还是 一次性
def create_session(name: str, is_save: bool = False) -> Session:
    if name in session_map or name in async_session_map:
        raise SessionExistException(f'Session [{name}] 已经存在')
    session = requests.Session()
    if is_save:
        save_session(name, session)
    return session


# 创建异步session | is_save: 是要保存至缓存 还是 一次性
def create_async_session(name: str, is_save: bool = False) -> AsyncSession:
    if name in session_map or name in async_session_map:
        raise SessionExistException(f'AsyncSession [{name}] 已经存在')
    async_session = requests.AsyncSession()
    if is_save:
        save_session(name, async_session)
    return async_session


# 手动关闭同步会话 | 一般建议走 close_session 入口
def _close_sync_session(name: str, session: Session):
    if isinstance(session, Session):
        session.close()
        session_map.pop(name)
    else:
        pass


# 手动关闭异步会话 | 一般建议走 close_session 入口
async def _close_async_session(name: str, session: AsyncSession):
    if isinstance(session, AsyncSession):
        await session.close()
        async_session_map.pop(name)
    else:
        pass
