"""把整条 pipeline 串起来：fetch -> store(去重) -> summarize -> deliver"""
import os
from dotenv import load_dotenv

from fetch import read_feeds, fetch_articles
from store import init_db, filter_new, mark_seen
from summarize.factory import get_summarizer
from deliver.email import build_html, send_email


def main():
    load_dotenv()

    feeds = read_feeds("feeds.txt")
    con = init_db(os.environ.get("DB_PATH", "seen.db"))

    new = filter_new(con, fetch_articles(feeds))
    if not new:
        print("没有新文章,今天不发。")
        return
    print(f"发现 {len(new)} 篇新文章,开始总结……")

    summarizer = get_summarizer(os.environ.get("SUMMARIZER", "claude"))
    items = [(a, summarizer.summarize(a)) for a in new]

    send_email(build_html(items))
    mark_seen(con, new)          # 发送成功后才标记,邮件失败则下次重试
    print(f"已推送 {len(items)} 篇。")


if __name__ == "__main__":
    main()