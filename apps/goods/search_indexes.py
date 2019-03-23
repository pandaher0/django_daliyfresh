# Author:hxj
from haystack import indexes
from apps.goods.models import GoodsSKU
#指定对于某个类的某些数据建立索引
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    # use_template=True指的是根据表中哪些字段生成索引文件，将说明存放在一个文件中
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return GoodsSKU

    def index_queryset(self, using=None):
        return self.get_model().objects.all()