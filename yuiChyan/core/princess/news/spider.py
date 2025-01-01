import abc
import re
from dataclasses import dataclass
from typing import List, Union

import httpx
from bs4 import BeautifulSoup

from yuiChyan.config import PROXY


@dataclass
class Item:
    idx: Union[str, int]
    content: str = ""

    def __eq__(self, other):
        return self.idx == other.idx


class BaseSpider(abc.ABC):
    url = None
    src_name = None
    header = {"Connection": "close"}
    idx_cache = set()
    item_cache = []

    @classmethod
    async def get_response(cls):
        proxy:str = None if cls.src_name == "国服官网" else PROXY
        async with httpx.AsyncClient(proxy=proxy) as session:
            resp = await session.get(cls.url, headers=cls.header, timeout=15)
        resp.raise_for_status()
        return resp

    @staticmethod
    @abc.abstractmethod
    async def get_items(resp) -> List[Item]:
        raise NotImplementedError

    @classmethod
    async def get_update(cls) -> List[Item]:
        resp = await cls.get_response()
        items = await cls.get_items(resp)
        updates = [i for i in items if i.idx not in cls.idx_cache]
        if updates:
            cls.idx_cache.update(i.idx for i in items)
            cls.item_cache = items
        return updates

    @classmethod
    def format_items(cls, items) -> str:
        return f'> PCR{cls.src_name}新闻\n' + '\n'.join(map(lambda i: i.content, items))


class TwSpider(BaseSpider):
    url = "http://www.princessconnect.so-net.tw/news/"
    src_name = "台服官网"

    @staticmethod
    async def get_items(resp):
        soup = BeautifulSoup(resp.text, 'lxml')
        return [
            Item(idx=dd.a["href"],
                 content=f"{dd.text}\n▲www.princessconnect.so-net.tw{dd.a['href']}"
                 ) for dd in soup.find_all("dd")
        ]


class BiliSpider(BaseSpider):
    url = "http://api.biligame.com/news/list?gameExtensionId=267&positionId=2&pageNum=1&pageSize=7&typeId="
    src_name = "国服官网"

    @staticmethod
    async def get_items(resp):
        content = resp.json()
        items = [
            Item(idx=n["id"],
                 content="{title}\n▲game.bilibili.com/pcr/news.html#detail={id}".format_map(n)
                 ) for n in content["data"]
        ]
        return items


class JpSpider(BaseSpider):
    url = "https://priconne-redive.jp/news/"
    src_name = "日服官网"
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/63.0.3239.132 Safari/537.36'
    }

    @staticmethod
    async def get_items(resp):
        data = resp.content
        data = data.decode()
        title = re.findall('<h4>(.*?)</h4>', data)  # 全部标题

        data_post_ids = re.findall('data-post-id="(.*[0-9])"', data)  # 全部ID
        items = []
        for i in range(len(title)):
            t = title[i]
            news_id = data_post_ids[i]
            items.append(Item(
                idx=news_id,
                content=f"{t}\n▲https://priconne-redive.jp/news/event/{news_id}/"
            ))
        return items
