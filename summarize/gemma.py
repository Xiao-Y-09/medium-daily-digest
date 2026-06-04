"""本地 Gemma 实现：通过 Ollama 调用本地模型做总结。"""
import json, os, re
import ollama
from models import Article, Summary
from summarize.base import Summarizer

PROMPT = """阅读下面这篇文章，用**中文**总结。只输出一个 JSON 对象，不要任何其它文字、不要 markdown 代码块：
{{"one_line": "一句话总结", "key_points": ["要点1", "要点2", "要点3"], "worth_reading": "high"}}

worth_reading 取值：high / medium / low，表示这篇值不值得花时间读全文。

标题：{title}
内容：{content}

重要：one_line 和 key_points 全部必须用中文。"""


def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            return json.loads(text[s : e + 1])
        raise


class GemmaSummarizer(Summarizer):
    def __init__(self):
        self.model = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

    def summarize(self, article: Article) -> Summary:
        resp = ollama.chat(
            model=self.model,
            messages=[{
                "role": "user",
                "content": PROMPT.format(title=article.title,
                                         content=article.content[:4000]),
            }],
            format="json",          # 让 Ollama 强制输出合法 JSON
        )
        data = _extract_json(resp["message"]["content"])
        return Summary(one_line=data["one_line"],
                       key_points=data["key_points"],
                       worth_reading=data["worth_reading"])