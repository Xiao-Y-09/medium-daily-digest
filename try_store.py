from fetch import fetch_articles
from store import init_db, filter_new, mark_seen

feeds = open("feeds.txt").read().split()
articles = fetch_articles(feeds)
con = init_db()

# 第一次:数据库是空的,应该全是"新"文章
new1 = filter_new(con, articles)
print("第一次 filter_new:", len(new1), "篇新文章")

# 标记成已读
mark_seen(con, new1)

# 第二次:同一批文章,应该一篇都不剩了
new2 = filter_new(con, articles)
print("第二次 filter_new:", len(new2), "篇新文章")