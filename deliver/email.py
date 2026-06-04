"""Deliver stage: 把总结拼成 HTML，通过 SMTP 发一封汇总邮件。"""
import os
import smtplib
from email.mime.text import MIMEText

from models import Article, Summary

_WORTH_LABEL = {"high": "值得读", "medium": "可看看", "low": "略过"}


def build_html(items: list[tuple[Article, Summary]]) -> str:
    """纯函数：拼 HTML，方便单测。"""
    blocks = []
    for art, s in items:
        points = "".join(f"<li>{p}</li>" for p in s.key_points)
        worth = _WORTH_LABEL.get(s.worth_reading, s.worth_reading)
        blocks.append(
            f'<div style="margin-bottom:24px">'
            f'<h3 style="margin:0 0 4px"><a href="{art.link}">{art.title}</a></h3>'
            f'<p style="margin:0 0 6px;color:#555">{s.one_line} <b>[{worth}]</b></p>'
            f'<ul style="margin:0">{points}</ul>'
            f"</div>"
        )
    return f"<h2>今日 Medium 摘要（{len(items)} 篇）</h2>" + "".join(blocks)


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