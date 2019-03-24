from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from apps.goods.models import GoodsSKU
from apps.user.models import Address
from apps.order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime


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


class OrderCommitView(View):
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
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

            count = conn.hget(cart_key, sku_id)

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

        # 清空购物车中对应商品
        conn.hdel(cart_key, *sku_ids)


        return JsonResponse({'res':5, 'data': '创建成功'})
