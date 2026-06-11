# PLANNING.md — Medium Daily Digest

## 1. 项目概述

一个 **LLM 驱动的信息聚合与摘要系统**:每天抓取我关注的 Medium 内容,用大模型归纳成结构化总结,发到我的邮箱,帮我快速决定哪些文章值得点进去读。

- **数据来源**:Medium RSS feed(作者 / publication / tag)
- **总结模型**:Claude API 与 本地 Gemma(Ollama)双实现,可切换、可对比
- **推送方式**:每天一封汇总 Email
- **运行方式**:MVP 阶段手动 `python main.py`,后续上 GitHub Actions 定时

> ⚠️ **已知限制**:Medium 付费墙后的文章在 RSS 里只有摘要,拿不到全文。免费文章一般能拿到较完整正文。所以总结质量对免费文章好,对会员文章退化为"基于摘要判断要不要读"。这是设计前提,不试图绕过付费墙。

---

## 2. MVP 范围 (v0.1)

**目标:最简单的、能端到端跑通的版本,且模块清晰、方便后续改。**

In scope（要做）:
- 从 `feeds.txt` 读取一组 RSS URL
- 抓取并解析文章(标题、链接、摘要/正文、发布时间)
- 用 SQLite 去重(只处理没见过的新文章)
- 调一个总结模型,输出结构化结果(一句话 + 3 要点 + 是否值得读)
- 拼成一封 HTML 邮件发出去
- 手动运行一次,完整跑通

Out of scope（先不做,但结构预留)— 见第 11 节:
- 兴趣/提示词过滤层
- 第二个模型(Gemma)—— 先让 Claude 一条路跑通,再补
- GitHub Actions 定时
- Embedding 语义筛选

---

## 3. Pipeline

```
feeds.txt
   │
   ▼
[ fetch ]  ── feedparser 抓取 + 解析 ──►  list[Article]
   │
   ▼
[ store ]  ── SQLite 去重,只留新文章 ──►  list[Article] (new only)
   │
   ▼
[ summarize ]  ── Summarizer 调模型 ──►  list[(Article, Summary)]
   │
   ▼
[ deliver ]  ── 拼 HTML + SMTP 发送 ──►  一封汇总邮件
```

未来加上过滤后(见第 11 节),pipeline 在 store 和 summarize 之间插入一层:

```
fetch → store(dedup) → filter → summarize → deliver
```

设计原则:**先用便宜手段粗筛,再对少数文章做贵的总结**(漏斗),省 token、省时间。

---

## 4. 目录结构

```
medium-digest/
├── feeds.txt              # 关注的 RSS URL,一行一个
├── .env                   # 密钥与配置(不进 git)
├── .env.example           # 配置模板(进 git)
├── requirements.txt
├── config.py              # 读取 .env,集中管理配置
├── models.py              # Article / Summary 数据结构
├── fetch.py               # 抓取 + 解析 RSS
├── store.py               # SQLite 去重
├── summarize/
│   ├── __init__.py
│   ├── base.py            # Summarizer 抽象基类
│   ├── claude.py          # Claude API 实现
│   ├── gemma.py           # 本地 Gemma / Ollama 实现(v0.1 可先留空)
│   └── factory.py         # 按配置返回对应 Summarizer
├── deliver/
│   ├── __init__.py
│   └── email.py           # 拼 HTML + SMTP 发送
├── main.py                # 串起整条 pipeline
└── tests/                 # 单元测试
    ├── test_fetch.py
    ├── test_store.py
    └── test_email.py
```

每个文件只负责一件事,这样既好测试,也方便单独替换。

---

## 5. 核心数据结构与接口

`models.py`:

```python
from dataclasses import dataclass

@dataclass
class Article:
    id: str          # 用 RSS 的 guid 或 link,作为去重主键
    title: str
    link: str
    content: str     # 摘要或正文(可能被付费墙截断)
    published: str   # ISO 时间字符串

@dataclass
class Summary:
    one_line: str           # 一句话总结
    key_points: list[str]   # 3 条要点
    worth_reading: str      # "high" | "medium" | "low"
```

`summarize/base.py` —— 这是双模型可切换的关键,典型的策略模式 + 依赖倒置:

```python
from abc import ABC, abstractmethod
from models import Article, Summary

class Summarizer(ABC):
    @abstractmethod
    def summarize(self, article: Article) -> Summary:
        """输入一篇文章,返回结构化总结。所有实现共享这个接口。"""
        ...
```

`summarize/factory.py`:

```python
from summarize.base import Summarizer

def get_summarizer(name: str) -> Summarizer:
    if name == "claude":
        from summarize.claude import ClaudeSummarizer
        return ClaudeSummarizer()
    if name == "gemma":
        from summarize.gemma import GemmaSummarizer
        return GemmaSummarizer()
    raise ValueError(f"unknown summarizer: {name}")
```

`main.py` 里只依赖抽象接口,不关心底下是哪个模型:

```python
summarizer = get_summarizer(config.SUMMARIZER)   # "claude" 或 "gemma"
```

---

## 6. 各模块职责

- **config.py**:用 `python-dotenv` 读 `.env`,把所有配置(API key、SMTP 信息、`SUMMARIZER` 选哪个、`DB_PATH`)集中成常量。其它模块只从这里拿配置,不直接读环境变量。
- **fetch.py**:`fetch_articles(feed_urls) -> list[Article]`。内部把"调 feedparser"和"把一条 entry 转成 Article"分成两个函数(`parse_entry` 是纯函数,方便测)。
- **store.py**:`init_db(path)`、`filter_new(articles) -> list[Article]`(只返回数据库里没有的)、`mark_seen(articles)`。SQLite 是 Python 标准库,零依赖。
- **summarize/**:每个实现都在 prompt 里**要求只输出固定字段的 JSON**,然后解析成 `Summary`。Gemma 那边要加容错解析 + 重试(小模型偶尔不守格式)。建议 prompt 里让它**用中文总结英文文章**。
- **deliver/email.py**:`build_html(items) -> str`(纯函数,易测)+ `send_email(html)`(唯一有副作用的部分)。每天**一封汇总邮件**,每篇 = 标题(超链接)+ 一句话 + 3 要点 + 是否值得读。
- **main.py**:按 pipeline 顺序把上面串起来,处理"今天没有新文章就不发"这类边界情况。

---

## 7. 配置与密钥

`feeds.txt`(一行一个 RSS URL):
```
https://medium.com/feed/tag/large-language-models
https://medium.com/feed/@some-author
https://medium.com/feed/towards-data-science
```

`.env.example`:
```
SUMMARIZER=claude            # claude | gemma
ANTHROPIC_API_KEY=sk-...
OLLAMA_MODEL=gemma2:9b        # 本地模型名
OLLAMA_HOST=http://localhost:11434
DB_PATH=seen.db

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=you@gmail.com
SMTP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # ⚠️ Gmail 应用专用密码,不是登录密码
EMAIL_TO=you@gmail.com
```

> ⚠️ **邮件坑**:不要用 Gmail 登录密码。开两步验证后生成一个 **App Password**,走 SSL(465 端口)用 `smtplib` 发。`.env` 一定加进 `.gitignore`。

---

## 8. 数据库 schema

```sql
CREATE TABLE IF NOT EXISTS seen_articles (
    id        TEXT PRIMARY KEY,   -- Article.id
    title     TEXT,
    link      TEXT,
    seen_at   TEXT                 -- ISO 时间戳
);
```

去重逻辑:`filter_new` 查 `id` 是否已存在;`mark_seen` 在成功推送后写入。

---

## 9. 单元化 / 可测试性原则

- **I/O 集中在边缘**:网络(fetch)、数据库(store)、模型调用(summarize)、SMTP(deliver)各自隔离,核心逻辑尽量是纯函数。
- **纯函数易测**:`parse_entry`、`build_html` 不碰外部世界,直接喂输入断言输出。
- **用接口隔离模型**:测 `main` 流程时,塞一个 `FakeSummarizer`(返回写死的 `Summary`),不真调 API。
- **测 store** 用临时 SQLite 文件 / `:memory:`,不污染真实库。
- 每个模块对外暴露的函数签名稳定,内部实现可随便换。

---

## 10. 落地顺序(MVP 优先,每步都可运行)

1. 搭骨架:`config.py` + `feeds.txt` + `.env`,跑通配置读取
2. `fetch.py`:抓一个 feed,把标题打印到终端 → 确认数据拿得到、长什么样
3. `store.py`:加 SQLite 去重,第二次运行应输出"0 篇新文章"
4. `summarize/base.py` + `factory.py` + `claude.py`:**先只接 Claude**,把总结打印到终端
5. `deliver/email.py`:发出第一封汇总邮件
6. `main.py`:把 2–5 串成完整 pipeline,手动跑通一次 → **v0.1 完成**
7. `summarize/gemma.py`:在同一接口下补上 Gemma,改 `.env` 的 `SUMMARIZER` 即可切换、对比
8. (之后)加过滤层、上 GitHub Actions —— 见第 11 节

---

## 11. 未来扩展点(结构已预留)

- **兴趣/提示词过滤**:在 `store` 和 `summarize` 之间插一个 `filter.py`。
  - v1:让总结模型顺手多输出一个"相关度"字段(几乎零成本)
  - v2:用 embedding 算我的兴趣描述与文章的 cosine 相似度做粗筛(复用 RAG 经验,便宜且快,适合文章量大时)
- **定时**:GitHub Actions 的 scheduled workflow,免费、不用自建服务器。把密钥放 repo secrets。
- **更多输出渠道**:`deliver/` 下加 `telegram.py` / `notion.py`,与 `email.py` 平级,互不影响。

---

## 12. 依赖 (requirements.txt)

```
feedparser
anthropic
python-dotenv
ollama          # 本地 Gemma,用 Ollama 时
```

`sqlite3`、`smtplib`、`email` 都是 Python 标准库,无需安装。
