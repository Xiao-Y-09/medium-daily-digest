"""本地 Gemma 实现：通过 Ollama 调用本地模型做总结。"""
import json, os, re
import ollama
from models import Article, Summary
from summarize.base import Summarizer
from profile import load_reader_profile

PROMPT = """你是一个帮特定读者筛选和精读文章的助手。下面是这位读者的画像，你要**站在他的角度**判断这篇文章对他的价值：

<读者画像>
{profile}
</读者画像>

请阅读文章，完成两件事：
1. 按读者画像给这篇文章打一个帮助度评分（score），1-10 的整数：
   - 8-10：内容扎实、有新东西、正好契合读者想学/想成长的方向
   - 4-7：有一定价值，但偏浅、或只是部分相关
   - 1-3：读者大概率不需要（入门内容他已会、纯营销/标题党/无干货）
   评分依据读者画像里的 Score HIGH / Score LOW 标准，不是这篇文章"客观上好不好"。
2. 用**中文**写总结，让读者不点开原文也能读懂文章讲了什么。detailed_summary 要写得详细、有结构、分段展开，像一篇精读笔记，而不是简短摘要。宁可长一些、讲透，也不要笼统。

只输出一个 JSON 对象，不要任何其它文字、不要 markdown 代码块：
{{"one_line": "一句话概括", "key_points": ["要点1", "要点2", "要点3"], "detailed_summary": "详细的替读正文，用 markdown 分成 2-4 个小段，每段一个小标题（用 ## 开头），展开讲清楚每部分'讲了什么、怎么做的、为什么'。要详细到读者不看原文也能完整理解。", "score": 7, "reason": "为什么给这个分（结合读者画像，一句话）"}}

标题：{title}
内容：{content}

重要：one_line、key_points、detailed_summary、reason 全部用中文；score 是 1-10 的整数；detailed_summary 里用 ## 做小标题、分段展开。"""


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
        self.model = os.environ.get("SUMMARIZE_MODEL", "gemma3:27b")
        self.profile = load_reader_profile()   # 启动时读一次画像,存起来复用

    def summarize(self, article: Article) -> Summary:
        resp = ollama.chat(
            model=self.model,
            messages=[{
                "role": "user",
                "content": PROMPT.format(
                    profile=self.profile,                 # ← 新增:把画像填进去
                    title=article.title,
                    content=article.content[:4000],
                ),
            }],
            format="json",
            options={"num_ctx": 8192},   # 限制上下文窗口,省显存
        )
        data = _extract_json(resp["message"]["content"])
        return Summary(
            one_line=data["one_line"],
            key_points=data["key_points"],
            detailed_summary=data["detailed_summary"],    # ← 新增字段
            score=data["score"],                          # ← 新增字段
            reason=data["reason"],                        # ← 新增字段
        )