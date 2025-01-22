import httpx
from httpx import AsyncClient, Client, Timeout

from yuiChyan.exception import *


# 封装的会话对象缓存
class SessionCache:

    def __init__(self,
                 name: Optional[str],
                 session: Optional[Client | AsyncClient],
                 proxy: Optional[str] = None,
                 timeout: Optional[Timeout] = None):
        # 会话名
        self.name = name
        # 会话
        self.session = session
        # 代理
        self.proxy = proxy
        # 超时时间
        self.timeout = timeout

    @classmethod
    def create_empty(cls):
        return cls(None, None)


# 高性能http请求工具session会话统一缓存
_session_map: dict[str, SessionCache] = {}
_async_session_map: dict[str, SessionCache] = {}


# 获取缓存的session | if_async: 是否是异步的session | create_if_none: 是否要在不存在的时候创建
def get_session_or_create(
        name: str,
        if_async: bool = False,
        proxy: Optional[str] = None,
        create_if_none: bool = True
) -> Client | AsyncClient:
    # 会话选择
    if if_async:
        # 异步会话
        current_map = _async_session_map
        create_session_func = create_async_session
        session_type = "AsyncClient"
    else:
        # 同步会话
        current_map = _session_map
        create_session_func = create_session
        session_type = "Client"
    # 获取缓存中的会话
    session: Optional[Client | AsyncClient] = current_map.get(name, SessionCache.create_empty()).session

    if session:
        return session
    if create_if_none:
        return create_session_func(name, True, proxy)

    raise SessionNotFoundException(f'找不到 {session_type} [{name}]')


# 重建已有的会话
def rebuild_session(name: str) -> Client:
    if name not in _session_map:
        raise SessionNotFoundException(f'找不到 Client [{name}]')
    session_cache = _session_map.get(name, SessionCache.create_empty())
    session_cache.session.close()
    return create_session(name, True, session_cache.proxy, session_cache.timeout)


# 重建已有的异步会话
async def rebuild_async_session(name: str) -> AsyncClient:
    if name not in _async_session_map:
        raise SessionNotFoundException(f'找不到 AsyncClient [{name}]')
    session_cache = _async_session_map.get(name, SessionCache.create_empty())
    await session_cache.session.aclose()
    return create_async_session(name, True, session_cache.proxy, session_cache.timeout)


# 手动关闭同步会话
def close_session(name: str, session: Client):
    if isinstance(session, Client):
        session.close()
        _session_map.pop(name)
    else:
        pass


# 手动关闭异步会话
async def close_async_session(name: str, session: AsyncClient):
    if isinstance(session, AsyncClient):
        await session.aclose()
        _async_session_map.pop(name)
    else:
        pass


# 创建同步session | is_save: 是要保存至缓存 还是 一次性
def create_session(name: str, is_save: bool = False, proxy: Optional[str] = None, timeout: Optional[Timeout] = None) -> Client:
    if name in _session_map or name in _async_session_map:
        raise SessionExistException(f'Session [{name}] 已经存在')
    # 设置默认超时时间
    timeout = timeout if timeout else Timeout(10, read=10)
    # 创建客户端
    session = httpx.Client(proxy=proxy, verify=False, timeout=timeout)
    if is_save:
        _save_session(name, session, proxy, timeout)
    return session


# 创建异步session | is_save: 是要保存至缓存 还是 一次性
def create_async_session(name: str, is_save: bool = False, proxy: Optional[str] = None, timeout: Optional[Timeout] = None) -> AsyncClient:
    if name in _session_map or name in _async_session_map:
        raise SessionExistException(f'AsyncSession [{name}] 已经存在')
    # 设置默认超时时间
    timeout = timeout if timeout else Timeout(10, read=10)
    # 创建客户端
    async_session = httpx.AsyncClient(proxy=proxy, verify=False, timeout=timeout)
    if is_save:
        _save_session(name, async_session, proxy, timeout)
    return async_session


# 保存session至缓存
def _save_session(name: str, session: Client | AsyncClient, proxy: Optional[str] = None, timeout: Optional[Timeout] = None):
    if isinstance(session, Client):
        _session_map[name] = SessionCache(name, session, proxy, timeout)
    elif isinstance(session, AsyncClient):
        _async_session_map[name] = SessionCache(name, session, proxy, timeout)
    else:
        raise SessionNotFoundException('不支持的 Session 类型，只支持 [Session] 和 [ClientSession]')
