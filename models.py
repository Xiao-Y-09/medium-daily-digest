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
    one_line: str
    key_points: list[str]
    worth_reading: str   # high / medium / low