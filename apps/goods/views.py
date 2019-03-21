from django.shortcuts import render
from django.views.generic import View
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection


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

        # 获取购物车中商品数目
        # 判断用户是否登录
        if request.user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % request.user.id
            cart_count = conn.hlen(cart_key)
        else:
            cart_count = 0

        context = {'types': types,
                   'goods_banners': goods_banners,
                   'promotion_banners': promotion_banners,
                   'cart_count': cart_count}

        return render(request, 'index.html', context)
