import feedparser
from models import Article

def read_feeds(path: str = "feeds.txt") -> list[str]:
    """从 feeds.txt 读取 RSS 链接，忽略空行和 # 开头的注释。"""
    urls = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls

def fetch_articles(feed_urls):
    articles = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        for e in feed.entries:
            articles.append(Article(
                id=e.get("id", e.link),
                title=e.title,
                link=e.link,
                content=e.get("summary", ""),
                published=e.get("published", ""),
            ))
    return articles