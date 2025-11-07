from typing import Optional, Dict, List

import feedparser
import httpx


class FeedEntry:
    """单条 RSS 订阅项"""
    def __init__(self, title: str, link: str, published: str, author: str,
                 summary: str, tags: List[str]):
        self.title = title
        self.link = link
        self.published = published
        self.author = author
        self.summary = summary
        self.tags = tags

    def __repr__(self):
        return f"<FeedEntry title='{self.title}'>"


class Feed:
    """RSS 整体信息"""
    def __init__(self, title: str, link: str, description: str, entries: List[FeedEntry]):
        self.title = title
        self.link = link
        self.description = description
        self.entries = entries

    def __repr__(self):
        return f"<Feed title='{self.title}' entries={len(self.entries)}>"

    def filter_by_tag(self, tag: str) -> List[FeedEntry]:
        """按标签筛选"""
        return [entry for entry in self.entries if tag in entry.tags]


class RSSParser:
    def __init__(self, source: str, proxy: Optional[dict] = None, timeout: int = 10):
        """
        初始化解析器
        :param source: RSS 的 URL 或本地文件路径
        :param proxy: 代理设置
        :param timeout: 请求超时时间（秒）
        """
        self.source = source
        self.proxy = proxy
        self.timeout = timeout

    def _fetch_content(self) -> str:
        """获取 RSS 内容（支持本地文件和网络请求）"""
        if self.source.startswith("http://") or self.source.startswith("https://"):
            resp = httpx.get(self.source, proxy=self.proxy, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text
        else:
            # 读取本地文件
            with open(self.source, "r", encoding="utf-8") as f:
                return f.read()

    def parse_dict(self) -> Dict:
        """解析 RSS 内容"""
        raw_content = self._fetch_content()
        feed = feedparser.parse(raw_content)

        result = {
            "title": feed.feed.get("title", ""),
            "link": feed.feed.get("link", ""),
            "description": feed.feed.get("description", ""),
            "entries": []
        }

        for entry in feed.entries:
            result["entries"].append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "author": entry.get("author", ""),
                "summary": entry.get("summary", ""),
                "tags": [tag["term"] for tag in entry.get("tags", [])]
            })
        return result

    def parse_feed(self) -> Feed:
        """解析 RSS，返回 Feed 对象"""
        raw_content = self._fetch_content()
        parsed = feedparser.parse(raw_content)

        entries = []
        for entry in parsed.entries:
            entries.append(FeedEntry(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                published=entry.get("published", ""),
                author=entry.get("author", ""),
                summary=entry.get("summary", ""),
                tags=[tag["term"] for tag in entry.get("tags", [])] if "tags" in entry else []
            ))

        return Feed(
            title=parsed.feed.get("title", ""),
            link=parsed.feed.get("link", ""),
            description=parsed.feed.get("description", ""),
            entries=entries
        )