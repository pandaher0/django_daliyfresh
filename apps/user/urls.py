# Author:hxj

from django.urls import include, re_path
from apps.user.views import *
from django.contrib.auth.decorators import login_required

app_name = 'user'

urlpatterns = [
    # re_path('^register$', views.register, name='register'),
    re_path('^register$', RegisterView.as_view(), name='register'),
    re_path('^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    re_path('^login$', LoginView.as_view(), name='login'),
    re_path('^logout$', LogoutView.as_view(), name='logout'),

    # re_path('^$', login_required(UserInfoView.as_view()), name='user'),
    # re_path('^order$', login_required(UserOrderView.as_view()), name='order'),
    # re_path('^address$', login_required(AddressView.as_view()), name='address'),

    re_path('^$', UserInfoView.as_view(), name='user'),
    re_path('^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),
    re_path('^address$', AddressView.as_view(), name='address'),

]
