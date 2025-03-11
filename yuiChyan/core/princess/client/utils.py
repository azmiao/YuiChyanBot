import json
import os
from asyncio import Lock
from enum import Enum
from typing import Optional, Union, List

import zhconv

from yuiChyan import CQEvent, CommandErrorException, InterFunctionException
from yuiChyan.config import PROXY
from yuiChyan.http_request import get_session_or_create
from yuiChyan.core.princess.client.game_client import PcrClient
from yuiChyan.core.princess.client.parse_client import ParseClient
from .player_pref import decrypt_xml

# 当前目录
current_path: str = os.path.dirname(__file__)
# 默认headers
default_headers: dict[str, str]= {
    "Accept": "*/*",
    "Accept-Encoding": "deflate, gzip",
    "User-Agent": "UnityPlayer/2021.3.27f1 (UnityWebRequest/1.0, libcurl/7.84.0-DEV)",
    "Content-Type": "application/octet-stream",
    "X-Unity-Version": "2021.3.27f1",
    "APP-VER": "5.0.0",
    "BATTLE-LOGIC-VERSION": "4",
    "DEVICE": "2",
    "DEVICE-ID": "1e4a1b03d1b6cd8a174a826f76e009f4",
    "DEVICE-NAME": "Xiaomi MI 9",
    "GRAPHICS-DEVICE-NAME": "Adreno (TM) 640",
    "IP-ADDRESS": "10.0.2.15",
    "LOCALE": "Jpn",
    "PLATFORM-OS-VERSION": "Android OS 15 / API-35 (AQ3A.240812.002/OS2.0.105.0.VFACNXM)",
    "RES-VER": "00420033"
}
# headers配置文件
header_path: str = os.path.join(current_path, 'headers.json')
# 缓存的 用户查询 用的客户端
user_client_cache: Optional[PcrClient] = None
user_lock: Lock = Lock()
# 缓存的 公会管理 用的客户端
admin_client_cache: Optional[PcrClient] = None
admin_lock: Lock = Lock()


# 客户端类型枚举类
class ClientType(Enum):
    USER = 'user'
    ADMIN = 'admin'
    PARSE = 'admin'  # 和 admin 用一样的配置就行


# 解析类型枚举类
class ParseType(Enum):
    REQUEST = 0
    RESPONSE = 1


# 获取服务器名称
def get_cx_name(cx):
    match cx:
        case '1':
            cx_name = '美食殿堂'
        case '2':
            cx_name = '真步王国'
        case '3':
            cx_name = '破晓之星'
        case '4':
            cx_name = '小小甜心'
        case _:
            cx_name = '未知'
    return cx_name


# 检验UID
async def judge_uid(uid_str: str, ev: CQEvent):
    # 校验数字
    try:
        int(uid_str)
    except TypeError or ValueError:
        raise CommandErrorException(ev, f'UID错误，需要10位纯数字，您输入了[{str(uid_str)}]')

    if len(uid_str) != 10:
        raise CommandErrorException(ev, f'UID长度错误，需要10位数字，您输入了[{str(len(uid_str))}]位数')

    # 校验服务器
    cx = uid_str[:1]
    if cx not in ['1', '2', '3', '4']:
        raise CommandErrorException(ev, f'UID校验出错，第一位数字为原始服务器ID，只能为1/2/3/4，您输入了[{str(uid_str)}]')
    # 排除1服的支持 | 反正这里也没有1服玩家
    if cx == '1':
        raise CommandErrorException(ev, f'UID校验失败，本客户端不提供1服的相关功能')


# 获取客户端 | 仅在需要的时候创建
async def get_client(clientType: ClientType) -> Union[PcrClient, ParseClient]:
    # 获取配置文件
    prefs_path = os.path.join(current_path, 'prefs_files', f'{clientType.value}_tw.sonet.princessconnect.v2.playerprefs.xml')
    if not os.path.isfile(prefs_path):
        raise InterFunctionException(f'{str(clientType.name)}客户端配置文件不存在，请检查！')

    # 校验headers文件是否存在
    if not os.path.isfile(header_path):
        # 没有文件 | 创建
        with open(header_path, 'w', encoding='utf-8') as _f:
            # noinspection PyTypeChecker
            json.dump(default_headers, _f, indent=4, ensure_ascii=False)

    # 匹配类型
    match clientType:
        case ClientType.USER:
            global user_client_cache
            if user_client_cache is None:
                info = decrypt_xml(prefs_path)
                user_client_cache = PcrClient(
                    info['UDID'],
                    info['SHORT_UDID'],
                    info['VIEWER_ID'],
                    info['TW_SERVER_ID'],
                    get_session_or_create(f'{str(clientType.name)}_Client', True, PROXY)
                )
            return user_client_cache
        case ClientType.ADMIN:
            global admin_client_cache
            if admin_client_cache is None:
                info = decrypt_xml(prefs_path)
                admin_client_cache = PcrClient(
                    info['UDID'],
                    info['SHORT_UDID'],
                    info['VIEWER_ID'],
                    info['TW_SERVER_ID'],
                    get_session_or_create(f'{str(clientType.name)}_Client', True, PROXY)
                )
            return admin_client_cache
        case _:
            # 解析客户端不用缓存直接重新生成
            info = decrypt_xml(prefs_path)
            parse_client = ParseClient(
                info['UDID'],
                info['VIEWER_ID'],
                info['TW_SERVER_ID']
            )
            return parse_client


# 获取异步锁
async def get_lock(clientType: ClientType) -> Lock:
    if clientType == ClientType.USER:
        return user_lock
    else:
        return admin_lock


# 更新客户端版本
async def update_client(version: str):
    # 读取下配置或直接拿默认的
    if not os.path.isfile(header_path):
        with open(header_path, 'r', encoding='utf-8') as _f:
            header_config = json.load(_f)
    else:
        header_config = default_headers
    # 更新版本并写入
    header_config['APP-VER'] = version
    with open(header_path, 'w', encoding='utf-8') as _f:
        # noinspection PyTypeChecker
        json.dump(header_config, _f, indent=4, ensure_ascii=False)
    # 然后去更新缓存的客户端版本
    global user_client_cache, admin_client_cache
    if not user_client_cache:
        user_client_cache.update_version(version)
    if not admin_client_cache:
        admin_client_cache.update_version(version)


# 由繁体转化为简体
def traditional_to_simplified(zh_str: str) -> str:
    return zhconv.convert(str(zh_str), 'zh-hans')


# 按步长分割字符串
def cut_str(obj: str, sec: int) -> list[str]:
    return [obj[i: i + sec] for i in range(0, len(obj), sec)]


# 解析hex字符串
def parse_hex(hex_string: str) -> (bytes, bytes):
    cleaned_hex_string = hex_string.strip().replace('\n', '')
    hex_parts = list(cleaned_hex_string.split())
    hex_parts = [hex_str.zfill(2) for hex_str in hex_parts]
    x_format = hex_to_bytes(hex_parts[:-32])
    key = hex_to_bytes(hex_parts[-32:])
    return x_format, key


# hex to utf-8
def hex_to_utf8(hex_list: List[str]) -> str:
    bytes_object = hex_to_bytes(hex_list)
    utf8_string = bytes_object.decode('utf-8', errors='ignore')
    return utf8_string


# hex to bytes
def hex_to_bytes(hex_list: List[str]) -> bytes:
    bytes_object = bytes.fromhex(''.join(hex_list))
    return bytes_object
