"""fetch -> store -> filter(门1) -> summarize+score(门3) -> 按分排序取topN -> deliver"""
import os
from dotenv import load_dotenv

from fetch import read_feeds, fetch_articles
from store import init_db, filter_new, mark_seen
from summarize.factory import get_summarizer
from deliver.email import build_html, send_email
from filter import filter_by_interest
from prefilter import prefilter

def main():
    load_dotenv()

    feeds = read_feeds("feeds.txt")
    con = init_db(os.environ.get("DB_PATH", "seen.db"))

    new = filter_new(con, fetch_articles(feeds))
    if not new:
        print("没有新文章,今天不发。")
        return
    
    # 按兴趣粗筛

    relevant = filter_by_interest(new)
    print(f"去重后 {len(new)} 篇,兴趣筛选后剩 {len(relevant)} 篇")
    if not relevant:
        print("没有相关文章,今天不发。")
        return

    # 门2:4b 便宜粗筛,砍掉明显垃圾,减轻 27b 负担
    candidates = prefilter(relevant)
    print(f"门1 后 {len(relevant)} 篇,门2 粗筛后剩 {len(candidates)} 篇")
    if not candidates:
        print("门2 后没有候选文章,今天不发。")
        return

    print(f"发现 {len(candidates)} 篇新文章,开始总结……")

    # avoid crash the whole pipeline just becasue one article fails to summarize.

    summarizer = get_summarizer(os.environ.get("SUMMARIZER", "gemma"))

    items = []
    for i, a in enumerate(candidates, 1):
        try:
            summary = summarizer.summarize(a)
            items.append((a, summary))
            print(f"  [{i}/{len(candidates)}] ✅ {a.title[:40]}")
        except Exception as e:
            print(f"  [{i}/{len(candidates)}] ❌ 跳过(出错): {a.title[:40]} —— {e}")

    if not items:
        print("所有文章都总结失败了,不发邮件。")

        return
    
    # 按帮助度评分过滤 + 排序,取最值得读的前 N 篇
    min_score = int(os.environ.get("MIN_SCORE", 6))
    max_items = int(os.environ.get("MAX_ITEMS", 10))

    # 1) 过滤:扔掉低于及格线的
    qualified = [(a, s) for (a, s) in items if s.score >= min_score]
    # 2) 排序:按 score 从高到低
    qualified.sort(key=lambda pair: pair[1].score, reverse=True)
    # 3) 截断:最多取 max_items 篇
    selected = qualified[:max_items]

    print(f"总结 {len(items)} 篇,达标(≥{min_score}) {len(qualified)} 篇,最终发送 {len(selected)} 篇")

    if not selected:
        print(f"没有文章达到及格线 {min_score},今天不发。")
        return

    send_email(build_html(selected))
    mark_seen(con, new)          # 发送成功后才标记,邮件失败则下次重试
    # todo: 这里会把筛选过的文章全标记为seen，即使是总结环节出问题了或者没发成 也会被放弃
    print(f"已推送 {len(selected)} 篇。")


if __name__ == "__main__":
    main()