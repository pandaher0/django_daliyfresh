from django.shortcuts import render, redirect
from django.urls import reverse

from apps.user.models import User
import re


# Create your views here.
# /user/register
def register(request):
    """显示注册页面"""
    return render(request, 'register.html')


def register_handle(request):
    """注册处理"""
    # 1.接收数据
    username = request.POST.get('user_name')
    pwd = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')
    # 2.进行数据校验
    if not all([username, pwd, email]):
        return render(request, 'register.html', {'errmsg': '数据不完整'})

    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不合法'})

    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请同意协议'})

    # 3.进行业务处理：用户注册
    user = User.objects.create_user(username, email, pwd)
    user.is_active = 0
    user.save()
    # 4.返回应答
    return redirect(reverse('goods:index'))
