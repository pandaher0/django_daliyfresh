# Author:hxj

from django.urls import include, re_path
from apps.user.views import RegisterView,ActiveView,LoginView

app_name = 'user'

urlpatterns = [
    # re_path('^register$', views.register, name='register'),
    re_path('^register$', RegisterView.as_view(), name='register'),
    re_path('^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    re_path('^login$', LoginView.as_view(), name='login'),
]
