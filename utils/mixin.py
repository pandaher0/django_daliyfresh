# Author:hxj

from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin

class LoginRequiredMixin(object):

    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类as_view
        view = super(LoginRequiredMixin,cls).as_view(**initkwargs)
        return login_required(view)

