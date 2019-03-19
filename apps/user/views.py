from http import cookies

from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.conf import settings
from apps.user.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
import re

# Create your views here.
# /user/register
from celery_task.tasks import send_register_active_email


class RegisterView(TemplateView):
    """注册"""

    def get(self, request, *args, **kwargs):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 2.进行数据校验
        if not all([username, pwd, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if pwd != cpwd:
            return render(request, 'register.html', {'errmsg': '两次密码不相同'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不合法'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 判断用户名是否已注册
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 3.进行业务处理：用户注册
        user = User.objects.create_user(username, email, pwd)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接
        # 激活连接中包含用户身份信息
        # 对用户信息进行加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)  # bytes类型
        token = token.decode('utf8')

        # 使用celery发送邮件
        send_register_active_email.delay(email, username, token)

        # 4.返回应答
        return redirect(reverse('goods:index'))


class ActiveView(TemplateView):
    """激活"""

    def get(self, request, *args, **kwargs):
        # def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            token = kwargs['token']
            info = serializer.loads(token)
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            return redirect(reverse('user:login'))

        except SignatureExpired as e:
            return HttpResponse('激活信息已过期')


class LoginView(TemplateView):
    def get(self, request, *args, **kwargs):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')

        if not all([username, pwd]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        user = authenticate(username=username, password=pwd)
        if user is not None:
            if user.is_active:
                # 记录用户登录状态
                login(request, user)

                response = redirect(reverse('goods:index'))

                # 判断是否记录用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名密码错误'})


# 信息管理
# /user
class UserInfoView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'user_center_info.html',{'page':'user'})


# 订单管理
# /user/order
class UserOrderView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'user_center_order.html',{'page':'order'})


# 地址管理
# /user/address
class AddressView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, 'user_center_site.html',{'page':'address'})
