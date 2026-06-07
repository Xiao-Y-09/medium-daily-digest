"""Filter stage: 用 embedding 语义相似度筛选,只保留和兴趣相关的文章。

输入：list[Article]
输出：和兴趣描述语义相似度超过阈值的文章
位置：在 store(去重)之后、summarize(总结)之前
"""
import os
import ollama
from models import Article

EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

# 你的兴趣描述,决定筛选方向。按自己想读的内容改。
# INTEREST = "大语言模型、RAG 检索增强生成、AI agent 智能体、LangChain、向量数据库与 embedding、提示工程、分布式系统与系统设计、模型推理优化"
INTEREST = "large language models, RAG retrieval augmented generation, AI agents, LangChain and LangGraph, vector databases and embeddings, prompt engineering, distributed systems and system design, model inference optimization"

# 相似度阈值,超过才保留。先用 0.45,之后按实际分布调。
THRESHOLD = float(os.environ.get("FILTER_THRESHOLD", "0.45"))


def _embed(text: str) -> list[float]:
    return ollama.embed(model=EMBED_MODEL, input=text)["embeddings"][0]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def filter_by_interest(articles: list[Article]) -> list[Article]:
    interest_vec = _embed(f"search_query: {INTEREST}")   # ← 查询加 search_query:
    kept = []
    for a in articles:
        text = f"{a.title}\n{a.content[:500]}"
        score = _cosine(interest_vec, _embed(f"search_document: {text}"))  # ← 文档加 search_document:
        if score >= THRESHOLD:
            kept.append(a)
    return kept