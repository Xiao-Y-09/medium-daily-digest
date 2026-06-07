"""门2:gemma 4b 便宜粗筛。只做二值 keep/drop,砍掉明显垃圾,拿不准就放行。"""
import json, os, re
import ollama
from models import Article

PREFILTER_PROMPT = """判断下面这篇文章是不是明显的低质内容(纯广告/软文、标题党、内容空洞、与技术和工程毫无关系)。

只输出一个 JSON 对象,不要其它文字:
{{"keep": true}}

规则:
- 只有当这篇**明显**是垃圾时才输出 {{"keep": false}}。
- 任何拿不准、或有可能有价值的,一律输出 {{"keep": true}}。
- 宁可放过,不可错杀。

标题:{title}
内容:{content}"""


def _extract_keep(text: str) -> bool:
    """容错解析,拿不到结果时默认 keep(放行),绝不因解析失败误杀。"""
    text = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        data = json.loads(text)
        return bool(data.get("keep", True))
    except (json.JSONDecodeError, AttributeError):
        return True   # 解析失败 → 放行,交给门3 精判


def prefilter(articles: list[Article]) -> list[Article]:
    model = os.environ.get("PREFILTER_MODEL", "gemma3:4b")
    kept = []
    for a in articles:
        try:
            resp = ollama.chat(
                model=model,
                messages=[{
                    "role": "user",
                    "content": PREFILTER_PROMPT.format(
                        title=a.title,
                        content=a.content[:800],   # 只看前800字,门2要便宜
                    ),
                }],
                format="json",
                options={"num_ctx": 2048},   # 输入短,上下文给小,更快更省显存
            )
            if _extract_keep(resp["message"]["content"]):
                kept.append(a)
        except Exception:
            kept.append(a)   # 出错也放行,绝不因门2 故障误杀
    return kept