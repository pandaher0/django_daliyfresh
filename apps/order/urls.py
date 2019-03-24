# Author:hxj

from django.urls import include, re_path
from apps.order.views import OrderPlaceView,OrderCommitView

app_name = 'order'

urlpatterns = [
    re_path('^place$', OrderPlaceView.as_view(), name='place'),
    re_path('^commit$', OrderCommitView.as_view(), name='commit'),
]
