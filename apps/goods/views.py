from django.core.paginator import Paginator
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
                       'spu_goods': spu_goods}

            return render(request, 'detail.html', context)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse('goods:index'))


# 种类id 页码 排序方式
# /list?type_id=种类id&page=页码&sort_by=排序方式
# /list/种类/页码?sort_by=排序方式
class ListView(View):
    def get(self, request, type_id, page):
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        types = GoodsType.objects.all()
        # default  id排序
        # price  price排序
        # hot   sales排序
        sort_by = request.GET.get('sort_by')
        if sort_by == 'price':
            sort = 'price'
        elif sort_by == 'hot':
            sort = '-sales'
        else:
            sort = '-id'
            sort_by = 'default'
        skus = GoodsSKU.objects.filter(type=type).order_by(sort)

        # 对数据进行分页
        paginator = Paginator(skus, 1)
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1
        if page == '':
            page = 1

        sku_page = paginator.page(page)
        # 只显示5页
        # 不足5页，全部显示
        # 前三页，显示1-5
        # 后三页，显示最后5页
        # 显示前两页和后2两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:5]

        if request.user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % request.user.id
            cart_count = conn.hlen(cart_key)
        else:
            cart_count = 0

        context = {'type': type,
                   'types': types,
                   'sku_page': sku_page,
                   'new_skus': new_skus,
                   'cart_count': cart_count,
                   'sort_by': sort_by,
                   'pages': pages}

        return render(request, 'list.html', context)
