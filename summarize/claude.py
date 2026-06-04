import json, os
from anthropic import Anthropic
from models import Summary
from summarize.base import Summarizer

PROMPT = """阅读下面这篇英文文章,用中文总结。只输出 JSON,不要任何别的文字:
{{"one_line":"一句话总结","key_points":["要点1","要点2","要点3"],"worth_reading":"high"}}

标题: {title}
内容: {content}"""

class ClaudeSummarizer(Summarizer):
    def __init__(self):
        self.client = Anthropic()              # 读环境变量 ANTHROPIC_API_KEY
        self.model = os.environ["CLAUDE_MODEL"]

    def summarize(self, article):
        msg = self.client.messages.create(
            model=self.model, max_tokens=500,
            messages=[{"role": "user",
                       "content": PROMPT.format(title=article.title,
                                                content=article.content[:4000])}])
        return Summary(**json.loads(msg.content[0].text))