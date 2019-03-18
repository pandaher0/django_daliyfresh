"""django_daliyfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('^tinymce/', include('tinymce.urls')),  # 富文本编辑器
    re_path('^user/', include('user.urls', namespace='user')),  # 用户
    re_path('^order/', include('order.urls', namespace='order')),  # 订单
    re_path('^cart/', include('cart.urls', namespace='cart')),  # 购物车
    re_path('^', include('goods.urls', namespace='goods')),  # 商品
]
