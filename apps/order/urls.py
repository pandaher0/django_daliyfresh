# Author:hxj

from django.urls import include, re_path
from apps.order.views import OrderPlaceView,OrderCommitView,OrderPayView,OrderCheckView,CommentView

app_name = 'order'

urlpatterns = [
    re_path('^place$', OrderPlaceView.as_view(), name='place'),
    re_path('^commit$', OrderCommitView.as_view(), name='commit'),
    re_path('^pay$', OrderPayView.as_view(), name='pay'),
    re_path('^check$', OrderCheckView.as_view(), name='check'),
    re_path('^comment/(?P<order_id>\d+)$', CommentView.as_view(), name='comment'),
]
