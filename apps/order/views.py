import time

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from apps.goods.models import GoodsSKU
from apps.user.models import Address
from apps.order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from datetime import datetime
from alipay import AliPay
from django.conf import settings
import os


# Create your views here.

class OrderPlaceView(LoginRequiredMixin, View):
    """订单页面"""

    def post(self, request):
        user = request.user
        # if not user.is_authenticated:
        #     return render(request, 'cart.html', {{'errmsg': '请先登录'}})

        sku_ids = request.POST.getlist('sku_ids')
        if not sku_ids:
            return redirect(reverse('cart:show'))

        skus = []
        total_count = 0
        total_price = 0
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
                count = conn.hget(cart_key, sku_id)
                amount = sku.price * int(count)
                sku.count = int(count)
                sku.amount = amount
                total_count += int(count)
                total_price += amount
                skus.append(sku)
            except GoodsSKU.DoesNotExist:
                return render(request, 'cart.html', {{'errmsg': '数据不完整'}})

        sku_ids = ','.join(sku_ids)

        # 运费 ：实际开发时是一个子系统
        transit_price = 10
        # 实付款：
        total_pay = total_price + transit_price

        # 获取用户收件地址
        address = Address.objects.filter(user=user)

        context = {'skus': skus,
                   'total_count': total_count,
                   'total_price': total_price,
                   'transit_price': transit_price,
                   'total_pay': total_pay,
                   'addrs': address,
                   'sku_ids': sku_ids}

        return render(request, 'place_order.html', context)


# 悲观锁
class OrderCommitView1(View):

    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登陆'})
        pay_style = request.POST.get('pay_style')
        addr_id = request.POST.get('addr_id')
        sku_ids = request.POST.get('sku_ids')

        if not all([pay_style, addr_id, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        if pay_style not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法支付方式'})

        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 订单id 20190324
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # total_count
        total_count = 0
        # total_price
        total_price = 0
        # transit_price
        transit_price = 10
        # 向Order_Info表中添加一条记录
        # 添加事务保存点
        save_id = transaction.savepoint()
        try:
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_style,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)
            # 连接redis
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            # 向Order_Goods表中添加记录
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                try:
                    # 悲观锁
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    # sku = GoodsSKU.objects.get(id=sku_id)

                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                count = conn.hget(cart_key, sku_id)
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '库存不足'})

                # origin_stock = count
                # new_stock = origin_stock - int(count)
                # new_sales = sku.sales + int(count)

                # 更新库存销量
                # 乐观锁
                # 返回受影响的行数
                # res = GoodsSKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                # if res == 0:
                #     transaction.savepoint_rollback(save_id)
                #     return JsonResponse({'res': 7, 'data': '下单失败'})

                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)
                # 更新库存销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # 计算总数量总价格
                amount = sku.price * int(count)
                total_price += amount
                total_count += int(count)

            # 更新order_info表总价格总数目
            order.total_count = total_count
            order.total_price = total_price
            order.save()


        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'data': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)
        # 清空购物车中对应商品
        conn.hdel(cart_key, *sku_ids)
        return JsonResponse({'res': 5, 'data': '创建成功'})


# 乐观锁
class OrderCommitView(View):
    """ mysql默认事务级别为repeated read 会导致幻读，重复读取，需要修改mysql配置文件，更改为read commited"""

    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登陆'})
        pay_style = request.POST.get('pay_style')
        addr_id = request.POST.get('addr_id')
        sku_ids = request.POST.get('sku_ids')

        if not all([pay_style, addr_id, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        if pay_style not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法支付方式'})

        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 订单id 20190324
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # total_count
        total_count = 0
        # total_price
        total_price = 0
        # transit_price
        transit_price = 10
        # 向Order_Info表中添加一条记录
        # 添加事务保存点
        save_point = transaction.savepoint()
        try:
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_style,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)
            # 连接redis
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            # 向Order_Goods表中添加记录
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):
                    try:
                        # 悲观锁
                        # sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                        sku = GoodsSKU.objects.get(id=sku_id)

                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    count = conn.hget(cart_key, sku_id)
                    if int(count) > sku.stock:
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'res': 6, 'errmsg': '库存不足'})

                    origin_stock = sku.stock
                    new_stock = origin_stock - int(count)
                    new_sales = sku.sales + int(count)

                    # 更新库存销量
                    # 乐观锁
                    # 返回受影响的行数
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                        sales=new_sales)
                    if res == 0:
                        # 尝试3次
                        if i == 2:
                            transaction.savepoint_rollback(save_point)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败'})
                        continue

                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)
                    # 更新库存销量
                    # sku.stock -= int(count)
                    # sku.sales += int(count)
                    # sku.save()

                    # 计算总数量总价格
                    amount = sku.price * int(count)
                    total_price += amount
                    total_count += int(count)

                    # 跳出循环
                    break

            # 更新order_info表总价格总数目
            order.total_count = total_count
            order.total_price = total_price
            order.save()


        except Exception as e:
            transaction.savepoint_rollback(save_point)
            return JsonResponse({'res': 7, 'data': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_point)
        # 清空购物车中对应商品
        conn.hdel(cart_key, *sku_ids)
        return JsonResponse({'res': 5, 'data': '创建成功'})


# 前端传递order_id
class OrderPayView(View):
    def post(self, request):
        # 校验登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '未登录'})

        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()

        alipay = AliPay(
            appid="2016092700606401",
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=True
        )

        total_pay = order.total_price + order.transit_price
        subject = "测试订单"

        # Pay via Web，open this url in your browser: https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_pay),
            subject=subject,
            return_url=None,
            notify_url=None  # this is optional
        )
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res':3,'pay_url':pay_url})


class OrderCheckView(View):
    def post(self,request):
        # 校验登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '未登录'})

        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()

        alipay = AliPay(
            appid="2016092700606401",
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=True
        )

        paid = False
        for i in range(10):
            time.sleep(3)
            result = alipay.api_alipay_trade_query(out_trade_no=order_id)
            if result.get('trade_status')=='TRADE_SUCCESS':
                trade_no = result.get('trade_no')
                order.trade_no = trade_no
                order.order_status = 4
                order.save()
                paid = True
                break

        if paid == False:
            return JsonResponse({'res': 3, 'errmsg': '支付失败'})
        else:
            return JsonResponse({'res': 4, 'msg': '支付成功'})

class CommentView(LoginRequiredMixin, View):
    """订单评论"""
    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count*order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i) # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '') # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5 # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))