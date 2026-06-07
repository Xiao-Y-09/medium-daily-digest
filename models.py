from dataclasses import dataclass

@dataclass
class Article:
    id: str
    title: str
    link: str
    content: str
    published: str

@dataclass
class Summary:
    one_line: str               # 一句话导语,扫读用
    key_points: list[str]       # 要点骨架
    detailed_summary: str       # 替读正文(新增,核心)
    score: int                  # 帮助度评分 1-10,排序+阈值用(原 worth_reading 升级)
    reason: str                 # 给这个分的简短理由(调试/评测 + 邮件可选展示)