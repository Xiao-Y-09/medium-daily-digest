from dotenv import load_dotenv
load_dotenv()                       # 必须在创建 ClaudeSummarizer 之前,先把 key 读进来

from fetch import read_feeds, fetch_articles
#from summarize.claude import ClaudeSummarizer
#from summarize.openai_llm import OpenAISummarizer

from summarize.gemma import GemmaSummarizer
# ...


articles = fetch_articles(read_feeds("feeds.txt"))
if not articles:
    print("没抓到文章,先检查 feeds.txt 里的链接")
    raise SystemExit

article = articles[0]               # 拿第一篇来测
print("测试文章:", article.title)
print("-" * 50)

# summarizer = ClaudeSummarizer()
# summary = summarizer.summarize(article)   # ← 这一行就是「喂」

# summarizer = OpenAISummarizer()
# summary = summarizer.summarize(article)

summarizer = GemmaSummarizer()
summary = summarizer.summarize(article)

print("一句话:", summary.one_line)
print("要点:")
for p in summary.key_points:
    print("  -", p)
print("值得读:", summary.worth_reading)