import hashlib
import random
import re
import time
import urllib.parse

from curl_cffi.requests import AsyncSession

from yuiChyan.http_request import get_session_or_create

# 主机URL
host_url = 'https://fanyi.youdao.com'
# 接口URL
api_url = 'https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
# 签名URL
get_sign_url = None
# 签名
sign_key = None


# 获取请求头
def get_headers(_host_url, if_api=False):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                 "Chrome/55.0.2883.87 Safari/537.36"

    if if_api:
        api_headers = {
            'Origin': urllib.parse.urlparse(_host_url).scheme + "://" + urllib.parse.urlparse(_host_url).hostname,
            'Referer': _host_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            "User-Agent": user_agent,
        }
        return api_headers
    else:
        host_headers = {
            'Referer': _host_url,
            "User-Agent": user_agent,
        }
        return host_headers


# 获取签名
async def get_sign_key(async_session: AsyncSession):
    global get_sign_url
    host_headers = get_headers(host_url, if_api=False)

    # 获取签名URL
    if not get_sign_url:
        host_html = await async_session.get(host_url, headers=host_headers, timeout=10)
        sign_pattern = r'https://shared.ydstatic.com/fanyi/newweb/(.*?)/scripts/newweb/fanyi.min.js'
        get_sign_url = re.compile(sign_pattern).search(host_html).group()

    # 新的签名接口
    r = await async_session.get(get_sign_url, headers=host_headers, timeout=10)
    r.raise_for_status()

    # 取出签名
    sign = re.compile(r'md5\("fanyideskweb" \+ e \+ i \+ "(.*?)"\)').findall(r.text)
    return sign[0] if sign and sign != [''] else "Ygy_4c=r#e#4EX^NUGUc5"  # v1.1.10


# 生成表单
async def get_form(query_text, api_headers, from_language, to_language, _sign_key):
    ts = str(int(time.time() * 1000))
    salt = str(ts) + str(random.randrange(0, 10))
    sign_text = ''.join(['fanyideskweb', query_text, salt, _sign_key])
    sign = hashlib.md5(sign_text.encode()).hexdigest()
    bv = hashlib.md5(api_headers['User-Agent'][8:].encode()).hexdigest()
    form = {
        'i': query_text,
        'from': from_language,
        'to': to_language,
        'lts': ts,  # r = "" + (new Date).getTime()
        'salt': salt,  # i = r + parseInt(10 * Math.random(), 10)
        'sign': sign,  # n.md5("fanyideskweb" + e + i + "n%A-rKaT5fb[Gy?;N5@Tj"),e=text
        'bv': bv,  # n.md5(navigator.appVersion)
        'smartresult': 'dict',
        'client': 'fanyideskweb',
        'doctype': 'json',
        'version': '2.1',
        'keyfrom': 'fanyi.web',
        'action': 'FY_BY_REALTlME'
    }
    return form


# 调用有道API
async def youdao_api(query_text: str, from_language: str = 'auto', to_language: str = 'zh'):
    global sign_key
    # 获取缓存或创建会话
    async_session = get_session_or_create('Youdao', True, True)

    # 获取签名
    if not sign_key:
        sign_key = await get_sign_key(async_session)

    # 翻译
    api_headers = get_headers(host_url, if_api=True)
    form = await get_form(query_text, api_headers, from_language, to_language, sign_key)
    r = async_session.post(api_url, data=form, headers=api_headers, timeout=10)
    r.raise_for_status()

    # 解析
    data = r.json()
    return '\n'.join([' '.join([it['tgt'] for it in item]) for item in data['translateResult']])
