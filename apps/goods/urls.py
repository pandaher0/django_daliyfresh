# Author:hxj

from django.urls import include, re_path
from apps.goods.views import IndexView
app_name = 'goods'

urlpatterns = [
    re_path('^$',IndexView.as_view(),name='index')
]