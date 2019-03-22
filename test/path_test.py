# Author:hxj
import os

from django.conf import settings
import os
import django
# 初始化
from django.template import loader

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_daliyfresh.settings')
django.setup()

# print(settings.STATICFILES_DIRS)
# save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
# print(save_path)

context = {}
temp = loader.get_template('static_index.html')
# 渲染页面
res_html = temp.render(context)
print(res_html)
# 生成文件
save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
with open(save_path, 'w',encoding='utf8') as f:
    f.write(res_html)
