# Author:hxj
# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
import os
import django

# 初始化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_daliyfresh.settings')
django.setup()

from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

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


@app.task
def generate_static_index_html():
    """产生首页静态页面"""
    # 获取商品的种类信息
    types = GoodsType.objects.all()
    # 获取首页轮播信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')
    # 获取首页促销信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    # 获取首页分类商品信息
    # type_goods_banner = IndexTypeGoodsBanner.objects.all()
    for type in types:
        imgae_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        type.image_banners = imgae_banners
        type.title_banners = title_banners

    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners}

    # 因为是静态文件，不需要生成httpresponse对象
    # 加载模板
    temp = loader.get_template('static_index.html')
    # 渲染页面
    res_html = temp.render(context)
    # 生成文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w', encoding='utf8') as f:
        f.write(res_html)
