# Author:hxj

from django.urls import include, re_path
from apps.cart.views import CartAddView,CartInfoView,CartUpdateView,CartDeleteView

app_name = 'cart'

urlpatterns = [
    re_path('^add$', CartAddView.as_view(), name='add'),
    re_path('^update$', CartUpdateView.as_view(), name='update'),
    re_path('^delete$', CartDeleteView.as_view(), name='delete'),
    re_path('^$', CartInfoView.as_view(), name='show'),
]
