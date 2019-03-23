# Author:hxj

from django.urls import include, re_path
from apps.goods.views import IndexView,DetailView,ListView
app_name = 'goods'

urlpatterns = [
    re_path('^index$',IndexView.as_view(),name='index'),
    re_path('^goods/(?P<goods_id>\d+)$',DetailView.as_view(),name='detail'),
    re_path('^list/(?P<type_id>\d+)/(?P<page>\d+)$',ListView.as_view(),name='list'),
]