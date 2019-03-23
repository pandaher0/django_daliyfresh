# Author:hxj

from django.urls import include, re_path
from apps.cart.views import CartAddView,CartInfoView

app_name = 'cart'

urlpatterns = [
    re_path('^add$', CartAddView.as_view(), name='add'),
    re_path('^$', CartInfoView.as_view(), name='show'),
]
