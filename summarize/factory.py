"""按名字返回对应的 Summarizer，由 .env 里的 SUMMARIZER 决定用哪个。"""
from summarize.base import Summarizer


def get_summarizer(name: str) -> Summarizer:
    if name == "claude":
        from summarize.claude import ClaudeSummarizer
        return ClaudeSummarizer()
    if name == "openai":
        from summarize.openai_llm import OpenAISummarizer
        return OpenAISummarizer()
    if name == "gemma":
        from summarize.gemma import GemmaSummarizer
        return GemmaSummarizer()
    raise ValueError(f"未知的 summarizer: {name}（可选 claude / openai / gemma）")