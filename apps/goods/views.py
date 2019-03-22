from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from apps.order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.cache import cache


# Create your views here.

# class Test(object):
#     def __init__(self):
#         self.name = 'abc'
#
# t = Test()
# t.age = 10
# print(t.age)


# http://127.0.0.1:8000
class IndexView(View):
    '''首页'''

    def get(self, request):
        '''显示首页'''
        # 获取缓存
        context = cache.get('index_page_data')
        if context is None:
            print('设置缓存')
            # 获取商品的种类信息
            types = GoodsType.objects.all()
            # 获取首页轮播信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')
            # 获取首页促销信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            # 获取首页分类商品信息
            # type_goods_banner = IndexTypeGoodsBanner.objects.all()
            for type in types:
                imgae_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
                type.image_banners = imgae_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners, }
            # 设置缓存
            cache.set('index_page_data', context, 3600)

        # 获取购物车中商品数目
        # 判断用户是否登录
        if request.user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % request.user.id
            cart_count = conn.hlen(cart_key)
        else:
            cart_count = 0

        context.update({'cart_count': cart_count})

        return render(request, 'index.html', context)


# http://127.0.0.1:8000/goods/商品id
class DetailView(View):
    """显示详情页"""

    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
            types = GoodsType.objects.all()
            # 获取不为空的评论
            orders = OrderGoods.objects.filter(sku=goods_id).exclude(comment='')
            # 新品信息
            new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:5]

            # 获取相同spu的商品
            spu_goods = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku.id)

            if request.user.is_authenticated:
                conn = get_redis_connection('default')
                cart_key = 'cart_%d' % request.user.id
                cart_count = conn.hlen(cart_key)
            else:
                cart_count = 0

            context = {'sku': sku,
                       'types': types,
                       'orders': orders,
                       'new_skus': new_skus,
                       'cart_count': cart_count,
                       'spu_goods':spu_goods}

            return render(request, 'detail.html',context)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse('goods:index'))
