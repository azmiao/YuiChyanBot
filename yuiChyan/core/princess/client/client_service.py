import json
from typing import Optional

import httpx

from yuiChyan.http_request import rebuild_async_session
from .game_client import ApiException, PreemptException
from .utils import get_client, ClientType, get_lock, ParseType, parse_hex


# 统一封装的接口请求
async def query_api(clientType: ClientType, api_uri: str, body: dict = None, retry_times: int = 1):
    # 获取对应客户端和锁
    query_client = await get_client(clientType)
    query_lock = await get_lock(clientType)
    # 请求
    last_exception: Optional[Exception] = None
    body = {} if not body else body
    for attempt in range(retry_times + 1):
        try:
            async with query_lock:
                # 如果需要登录就进行登录
                if query_client.shouldLogin:
                    await query_client.login()
                res = await query_client.callapi(api_uri, body)
            return res
        except PreemptException as e:
            # 被挤号了 | 不需要重试
            query_client.shouldLogin = True
            last_exception = e
            break
        except ApiException as e:
            # 一般的请求异常 | 可尝试一次重新登录请求
            query_client.shouldLogin = True
            last_exception = e
        except httpx.TransportError as e:
            # 特殊的请求异常 | 可能需要重建会话重新登录
            query_client.shouldLogin = True
            last_exception = e
            # 重建并更新会话至客户端
            async_session = await rebuild_async_session(f'{str(clientType.name)}_Client')
            query_client.update_async_session(async_session)
        except Exception as e:
            # 其他未知异常 | 可尝试一次重新登录请求
            query_client.shouldLogin = True
            last_exception = e
        # 超过重试次数了
        if attempt == retry_times:
            break

    # 最后抛出异常
    raise last_exception


# 统一封装的解析数据
async def parse_data(parseType: ParseType, data: str):
    parse_client = await get_client(ClientType.PARSE)
    if parseType == ParseType.REQUEST:
        x_format, key = parse_hex(data)
        result = parse_client.parse_request(x_format, key)
    else:
        result = parse_client.parse_response(data.encode('utf8'))
    return json.dumps(result)

