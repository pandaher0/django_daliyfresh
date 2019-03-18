# Author:hxj

from django.urls import include, re_path
from apps.goods import views
app_name = 'goods'

urlpatterns = [
    re_path('^$',views.index,name='index')
]