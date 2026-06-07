"""Deliver stage: 把总结拼成 HTML，通过 SMTP 发一封汇总邮件。"""
import os
import smtplib
import markdown

from email.mime.text import MIMEText

from models import Article, Summary

_WORTH_LABEL = {"high": "值得读", "medium": "可看看", "low": "略过"}


def build_html(items: list[tuple[Article, Summary]]) -> str:
    """纯函数：卡片式布局 + 按分数分组。"""

    def score_color(score: int) -> str:
        if score >= 8:
            return "#16a34a"
        if score >= 6:
            return "#ca8a04"
        return "#888"

    def render_card(art: Article, s: Summary) -> str:
        points = "".join(f'<li style="margin:4px 0">{p}</li>' for p in s.key_points)
        body = markdown.markdown(s.detailed_summary)
        color = score_color(s.score)
        return (
            f'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;'
            f'padding:20px 24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.04)">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">'
            f'<h2 style="margin:0;font-size:18px;line-height:1.4">'
            f'<a href="{art.link}" style="color:#111;text-decoration:none">{art.title}</a></h2>'
            f'<span style="flex-shrink:0;background:{color};color:#fff;font-size:13px;'
            f'font-weight:bold;padding:2px 10px;border-radius:999px">{s.score}/10</span>'
            f'</div>'
            f'<p style="margin:8px 0 0;color:#666;font-size:13px;line-height:1.5">💡 {s.reason}</p>'
            f'<p style="margin:14px 0 6px;font-size:15px;font-weight:600;color:#111">{s.one_line}</p>'
            f'<ul style="margin:6px 0 16px;padding-left:20px;color:#374151;font-size:14px">{points}</ul>'
            f'<div style="color:#374151;font-size:14px;line-height:1.7;'
            f'border-top:1px solid #f0f0f0;padding-top:14px">{body}</div>'
            f'</div>'
        )

    def render_group(title: str, group: list[tuple[Article, Summary]]) -> str:
        if not group:
            return ""
        cards = "".join(render_card(art, s) for art, s in group)
        return (
            f'<h2 style="font-size:15px;color:#555;margin:28px 0 12px;'
            f'padding-bottom:6px;border-bottom:2px solid #e5e7eb">{title}</h2>'
            f'{cards}'
        )

    # 按分数分组(items 已在 main 里按分数降序排好)
    top = [(a, s) for a, s in items if s.score >= 8]
    mid = [(a, s) for a, s in items if 6 <= s.score < 8]
    low = [(a, s) for a, s in items if s.score < 6]

    body_html = (
        render_group("⭐ 强烈推荐", top)
        + render_group("值得一看", mid)
        + render_group("其他", low)
    )

    header = (
        f'<div style="max-width:680px;margin:0 auto;font-family:'
        f'-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;'
        f'background:#f7f7f8;padding:24px 16px">'
        f'<h1 style="font-size:22px;color:#111;margin:0 0 4px">📬 今日 Medium 摘要</h1>'
        f'<p style="color:#888;font-size:13px;margin:0 0 20px">共 {len(items)} 篇 · 按帮助度排序</p>'
    )
    return header + body_html + "</div>"


def send_email(html: str) -> None:
    """唯一有副作用的部分：真正连服务器发信。"""
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_APP_PASSWORD"]

    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = "今日 Medium 摘要"
    msg["From"] = user
    msg["To"] = os.environ["EMAIL_TO"]

    with smtplib.SMTP_SSL(host, port) as server:
        server.login(user, password)
        server.send_message(msg)