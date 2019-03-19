# Author:hxj
# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import os
import django

# 初始化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_daliyfresh.settings')
django.setup()

app = Celery('celery_task.tasks', broker='redis://127.0.0.1:6379/8')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    # 发邮件
    subject = '邮件主题'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_msg = '<h1>%s您好</h1>邮件正文<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8080/user/active/%s</a>' % (
        username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_msg)
