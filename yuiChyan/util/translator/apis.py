import hashlib
import random
import re
import time
import urllib.parse
from typing import Optional, Tuple

from httpx import Client, AsyncClient

from yuiChyan import TranslatorError
from yuiChyan.http_request import get_session_or_create, close_session


class Tse:
    def __init__(self):
        self.author = 'Ulion.Tse'
        self.begin_time = time.time()
        self.default_session_seconds = 1.5e3
        self.transform_en_translator_pool = ('itranslate', 'lingvanex', 'myMemory', 'apertium', 'cloudTranslation',
                                             'translateMe')
        self.auto_pool = ('auto', 'detect', 'auto-detect', 'all')
        self.zh_pool = ('zh', 'zh-CN', 'zh-cn', 'zh-CHS', 'zh-Hans', 'zh-Hans_CN', 'cn', 'chi', 'Chinese')

    @staticmethod
    def get_headers(host_url, if_api=False, if_referer_for_host=True, if_ajax_for_api=True, if_json_for_api=False):
        url_path = urllib.parse.urlparse(host_url).path
        user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                     "Chrome/55.0.2883.87 Safari/537.36"
        host_headers = {
            'Referer' if if_referer_for_host else 'Host': host_url,
            "User-Agent": user_agent,
        }
        api_headers = {
            'Origin': host_url.split(url_path)[0] if url_path else host_url,
            'Referer': host_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            "User-Agent": user_agent,
        }
        if if_api and not if_ajax_for_api:
            api_headers.pop('X-Requested-With')
            api_headers.update({'Content-Type': 'text/plain'})
        if if_api and if_json_for_api:
            api_headers.update({'Content-Type': 'application/json'})
        return host_headers if not if_api else api_headers

    def check_en_lang(self, from_lang: str, to_lang: str, default_translator: Optional[str] = None, default_lang: str = 'en-US') -> Tuple[str, str]:
        if default_translator and default_translator in self.transform_en_translator_pool:
            from_lang = default_lang if from_lang == 'en' else from_lang
            to_lang = default_lang if to_lang == 'en' else to_lang
            from_lang = default_lang.replace('-', '_') if default_translator == 'lingvanex' and from_lang[:3] == 'en-' else from_lang
            to_lang = default_lang.replace('-', '_') if default_translator == 'lingvanex' and to_lang[:3] == 'en-' else to_lang
        return from_lang, to_lang

    def check_language(self,
                       from_language: str,
                       to_language: str,
                       language_map: dict,
                       output_auto: str = 'auto',
                       output_zh: str = 'zh',
                       output_en_translator: Optional[str] = None,
                       output_en: str = 'en-US',
                       if_check_lang_reverse: bool = True,
                       ) -> Tuple[str, str]:

        if output_en_translator:
            from_language, to_language = self.check_en_lang(from_language, to_language, output_en_translator, output_en)

        from_language = output_auto if from_language in self.auto_pool else from_language
        from_language = output_zh if from_language in self.zh_pool else from_language
        to_language = output_zh if to_language in self.zh_pool else to_language

        if from_language != output_auto and from_language not in language_map:
            raise TranslatorError('Unsupported from_language[{}] in {}.'.format(from_language, sorted(language_map.keys())))
        elif to_language not in language_map and if_check_lang_reverse:
            raise TranslatorError('Unsupported to_language[{}] in {}.'.format(to_language, sorted(language_map.keys())))
        elif from_language != output_auto and to_language not in language_map[from_language]:
            raise TranslatorError('Unsupported translation: from [{0}] to [{1}]!'.format(from_language, to_language))
        elif from_language == to_language:
            raise TranslatorError(f'from_language[{from_language}] and to_language[{to_language}] should not be same.')
        return from_language, to_language


class Youdao(Tse):
    def __init__(self):
        super().__init__()
        self.host_url = 'https://fanyi.youdao.com'
        self.api_url = 'https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        self.language_url = 'https://api-overmind.youdao.com/openapi/get/luna/dict/luna-front/prod/langType'
        self.get_sign_old_url = 'https://shared.ydstatic.com/fanyi/newweb/v1.0.29/scripts/newweb/fanyi.min.js'
        self.get_sign_url = None
        self.get_sign_pattern = 'https://shared.ydstatic.com/fanyi/newweb/(.*?)/scripts/newweb/fanyi.min.js'
        self.host_headers = self.get_headers(self.host_url, if_api=False)
        self.api_headers = self.get_headers(self.host_url, if_api=True)
        self.language_map = None
        self.session: Optional[Client] = None
        self.sign_key = None
        self.query_count = 0
        self.output_zh = 'zh-CHS'
        self.input_limit = 5000
        self.default_from_language = self.output_zh

    async def get_sign_key(self, host_html, session: AsyncClient, timeout):
        try:
            if not self.get_sign_url:
                self.get_sign_url = re.compile(self.get_sign_pattern).search(host_html).group()
            r = await session.get(self.get_sign_url, headers=self.host_headers, timeout=timeout)
            r.raise_for_status()
        except:
            r = await session.get(self.get_sign_old_url, headers=self.host_headers, timeout=timeout)
            r.raise_for_status()
        sign = re.compile('md5\\("fanyideskweb" \\+ e \\+ i \\+ "(.*?)"\\)').findall(r.text)
        return sign[0] if sign and sign != [''] else "Ygy_4c=r#e#4EX^NUGUc5"  # v1.1.10

    async def get_form(self, query_text, from_language, to_language, sign_key):
        ts = str(int(time.time() * 1000))
        salt = str(ts) + str(random.randrange(0, 10))
        sign_text = ''.join(['fanyideskweb', query_text, salt, sign_key])
        sign = hashlib.md5(sign_text.encode()).hexdigest()
        bv = hashlib.md5(self.api_headers['User-Agent'][8:].encode()).hexdigest()
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
            'action': 'FY_BY_REALTlME',  # not time.["FY_BY_REALTlME", "FY_BY_DEFAULT", "FY_BY_CLICKBUTTION", "lan-select"]
            # 'typoResult': 'false'
        }
        return form

    @staticmethod
    async def get_language_map(lang_url: str, session: AsyncClient, headers: dict, timeout: Optional[float]) -> dict:
        _data = await session.get(lang_url, headers=headers, timeout=timeout)
        data = _data.json()
        lang_list = sorted([it['code'] for it in data['data']['value']['textTranslate']['specify']])
        return {}.fromkeys(lang_list, lang_list)

    async def youdao_api(self, query_text: str, from_language: str = 'auto', to_language: str = 'en', **kwargs):
        timeout = kwargs.get('timeout', 10)
        is_detail_result = kwargs.get('is_detail_result', False)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        update_session_after_seconds = kwargs.get('update_session_after_seconds', self.default_session_seconds)

        not_update_cond_time = 1 if time.time() - self.begin_time < update_session_after_seconds else 0
        if not (self.session and not_update_cond_time and self.language_map and self.sign_key):
            # 超时了就先关闭
            close_session('Youdao', self.session)
            self.session: AsyncClient = get_session_or_create('Youdao', True)
            host_html = await self.session.get(self.host_url, headers=self.host_headers, timeout=timeout)
            self.sign_key = await self.get_sign_key(host_html.text, self.session, timeout)
            self.language_map = await self.get_language_map(self.language_url, self.session, self.host_headers, timeout)

        from_language, to_language = self.check_language(from_language, to_language, self.language_map, output_zh=self.output_zh)

        form = await self.get_form(query_text, from_language, to_language, self.sign_key)
        r = await self.session.post(self.api_url, data=form, headers=self.api_headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        time.sleep(sleep_seconds)
        self.query_count += 1
        assert 'translateResult' in data, f'API返回{str(data)}'
        return data if is_detail_result else '\n'.join(
            [' '.join([it['tgt'] for it in item]) for item in data['translateResult']])
