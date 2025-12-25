from datetime import datetime, timezone
from typing import Dict, List

import feedparser
from httpx import AsyncClient, HTTPStatusError

from yuiChyan.http_request import get_session_or_create, rebuild_async_session
from yuiChyan.util.date_utils import parse_datetime


class FeedEntry:
    """单条 RSS 订阅项"""
    def __init__(self, title: str, link: str, update_time_str: str, author: str, summary: str, tags: List[str]):
        self.title = title
        self.link = link
        self.update_time_str = update_time_str
        self.update_time: datetime | None = parse_datetime(update_time_str)
        self.author = author
        self.summary = summary
        self.tags = tags

    def __repr__(self):
        return f"<FeedEntry title='{self.title}'>"

    def __lt__(self, other):
        """按更新时间进行比较（早于返回 True）"""
        if not isinstance(other, FeedEntry):
            return NotImplemented
        # 如果没有时间，则按 datetime.min
        self_time = self.update_time or datetime.min.replace(tzinfo=timezone.utc)
        other_time = other.update_time or datetime.min.replace(tzinfo=timezone.utc)
        return self_time < other_time

class Feed:
    """RSS 整体信息"""
    def __init__(self, title: str, link: str, update_time_str: str, description: str, entries: List[FeedEntry]):
        self.title = title
        self.link = link
        self.update_time_str = update_time_str
        self.update_time = parse_datetime(update_time_str)
        self.description = description
        self.entries = entries

    def __repr__(self):
        return f"<Feed title='{self.title}' entries={len(self.entries)}>"

    def filter_by_tag(self, tag: str) -> List[FeedEntry]:
        """按标签筛选"""
        return [entry for entry in self.entries if tag in entry.tags]


class RSSParser:
    def __init__(self, source: str, proxy: str | None = None, timeout: int = 10, headers: dict | None = None):
        """
        初始化解析器
        :param source: RSS 的 URL 或本地文件路径
        :param proxy: 代理设置
        :param timeout: 请求超时时间（秒）
        :param headers: 请求头
        """
        self.source = source
        self.proxy = proxy
        self.timeout = timeout
        self.headers = headers

    async def _fetch_content(self) -> str:
        """获取 RSS 内容（支持本地文件和网络请求）"""
        if self.source.startswith("http://") or self.source.startswith("https://"):
            return await self._request_url()
        else:
            # 读取本地文件
            with open(self.source, "r", encoding="utf-8") as f:
                return f.read()

    async def _request_url(self):
        async_session: AsyncClient = get_session_or_create('RSSParser', True, self.proxy)
        try:
            resp = await async_session.get(self.source, timeout=self.timeout, headers=self.headers)
        except Exception:
            # 出现异常就重建会话再试一次
            async_session = await rebuild_async_session('RSSParser')
            resp = await async_session.get(self.source, timeout=self.timeout, headers=self.headers)
        resp.raise_for_status()
        return resp.text

    async def parse_dict(self) -> Dict:
        """解析 RSS 内容"""
        raw_content = await self._fetch_content()
        feed = feedparser.parse(raw_content)

        result = {
            "title": feed.feed.get("title", ""),
            "link": feed.feed.get("link", ""),
            "update_time_str": feed.feed.get("published", feed.feed.get("updated", "")),
            "description": feed.feed.get("description", ""),
            "entries": []
        }

        for entry in feed.entries:
            result["entries"].append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "update_time_str": entry.get("published", entry.get("updated", "")),
                "author": entry.get("author", ""),
                "summary": entry.get("summary", ""),
                "tags": [tag["term"] for tag in entry.get("tags", [])]
            })
        return result

    async def parse_feed(self) -> Feed:
        """解析 RSS，返回 Feed 对象"""
        raw_content = await self._fetch_content()
        parsed = feedparser.parse(raw_content)

        entries = []
        for entry in parsed.entries:
            entries.append(FeedEntry(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                update_time_str=entry.get("published", entry.get("updated", "")),
                author=entry.get("author", ""),
                summary=entry.get("summary", ""),
                tags=[tag["term"] for tag in entry.get("tags", [])] if "tags" in entry else []
            ))

        return Feed(
            title=parsed.feed.get("title", ""),
            link=parsed.feed.get("link", ""),
            update_time_str=parsed.feed.get("published", parsed.feed.get("updated", "")),
            description=parsed.feed.get("description", ""),
            entries=entries
        )