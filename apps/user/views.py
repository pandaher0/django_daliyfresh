from http import cookies

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView,View
from django.conf import settings
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
# from utils.mixin import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
# from redis import StrictRedis
from django_redis import get_redis_connection
import re

# Create your views here.
# /user/register
from celery_task.tasks import send_register_active_email


class RegisterView(View):
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


class ActiveView(View):
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


class LoginView(View):
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

                # 获取用户登录后跳转的地址
                # next=/user/order
                # key,default=None
                # 默认首页
                next_url = request.GET.get('next', reverse('goods:index'))

                response = redirect(next_url)

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


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        # logout函數清除session
        logout(request)
        return redirect(reverse('goods:index'))


# 信息管理
# /user
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # page = 'user
        # request.user request对象自动创建实例
        # 如果未登录 为AnonymousUser实例
        # 如果已登录，为User实例
        # request.user.is_authenticated()
        # 调用is_authenticated方法，登录为True，未登录为False
        # 并且在向模板文件传递变量时，会将request.user一并传递

        # 获取用户个人信息
        addr = Address.objects.get_default_addr(request.user)

        # 获取最近浏览
        # sr = StrictRedis(host='127.0.0.1', port=6379, db=9)
        con = get_redis_connection('default')

        history_key = 'history_%d' % request.user.id
        # 获取最近5个商品id
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库查询商品 无序
        goods = []

        for id in sku_ids:
            good = GoodsSKU.objects.get(id=id)
            goods.append(good)

        return render(request, 'user_center_info.html', {'page': 'user', 'addr': addr,'goods':goods})


# 订单管理
# /user/order
class UserOrderView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # 获取订单信息

        return render(request, 'user_center_order.html', {'page': 'order'})


# 地址管理
# /user/address
class AddressView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        address = Address.objects.get_default_addr(request.user)
        # 获取默认收货地址
        return render(request, 'user_center_site.html', {'page': 'address', 'addr': address})

    def post(self, request):
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zipcode = request.POST.get('zipcode')
        phone = request.POST.get('phone')

        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        if not re.match(r'^1(3|4|5|7|8)\d{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号不合法'})

        # 如果已存在默认地址，新添加的不作为默认，否则为默认
        user = request.user
        address = Address.objects.get_default_addr(user)

        if address:
            is_default = False
        else:
            is_default = True

        Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zipcode, phone=phone,
                               is_default=is_default)

        return redirect(reverse('user:address'))
