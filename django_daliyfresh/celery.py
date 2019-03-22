# Author:hxj
from celery import Celery
from django.conf import settings
import os
import django
# 为celery设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_daliyfresh.settings')
# django.setup()

# 创建应用
app = Celery("celery_task.tasks")
# 配置应用
app.conf.update(
    # 配置broker, 这里我们用redis作为broker
    BROKER_URL='redis://127.0.0.1:6379/8',
)
# 设置app自动加载任务
# 从已经安装的app中查找任务
app.autodiscover_tasks(settings.INSTALLED_APPS)