from typing import Dict

from curl_cffi import requests
from curl_cffi.requests import AsyncSession, Session

from yuiChyan.exception import *

# 高性能http请求工具session会话统一缓存
session_map: Dict[str, Session] = {}
async_session_map: Dict[str, AsyncSession] = {}


# 获取缓存的session
def get_session(name: str) -> Session | AsyncSession:
    if name not in session_map and name not in async_session_map:
        raise SessionNotFoundException(f'session [{name}] not found!')
    elif name in session_map:
        return session_map.get(name)
    else:
        return async_session_map.get(name)


# 保存session
def set_session(name: str, session: Session | AsyncSession):
    if isinstance(session, Session):
        session_map[name] = session
    elif isinstance(session, AsyncSession):
        async_session_map[name] = session
    else:
        raise SessionNotFoundException('Unsupported type!')


# 创建同步session
def create_session(name: str, is_save: bool = False) -> Session:
    if name in session_map or name in async_session_map:
        raise SessionExistException(f'session [{name}] is already exist!')
    session = requests.Session()
    if is_save:
        set_session(name, session)
    return session


# 创建异步session
def create_async_session(name: str, is_save: bool = False) -> AsyncSession:
    if name in session_map or name in async_session_map:
        raise SessionExistException(f'async_session [{name}] is already exist!')
    async_session = requests.AsyncSession()
    if is_save:
        set_session(name, async_session)
    return async_session
