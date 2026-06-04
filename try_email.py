from dotenv import load_dotenv
load_dotenv()

from deliver.email import send_email

print("正在发送测试邮件...")
send_email("<h2>测试成功 ✅</h2><p>这是 medium-digest 发出的第一封邮件。</p>")
print("发送完成,去收件箱看看(也翻一下垃圾邮件)")