# Author:hxj

from django.urls import include, re_path
from apps.user import views

app_name = 'user'

urlpatterns = [
    re_path('^register$', views.register, name='register'),
    re_path('^register_handle$', views.register_handle, name='register_handle'),
]
