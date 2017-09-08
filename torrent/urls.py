from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'^keyboard/',views.keyboard),
        url(r'^message',views.first),
        url(r'^crawl/',views.parse_list),
        url(r'^delete/',views.del_old),
]
