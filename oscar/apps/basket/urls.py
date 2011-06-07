from django.conf.urls.defaults import patterns, url
from oscar.apps.basket.views import BasketView, SavedView, VoucherView, VoucherAddView, BasketAddView

urlpatterns = patterns('',                   
    url(r'^$', BasketView.as_view(), name='basket'),
    url(r'^add/$', BasketAddView.as_view(), name='basket-add'),    
    url(r'^vouchers/$', VoucherView.as_view(), name='basket-vouchers'),
    url(r'^vouchers/add/$', VoucherAddView.as_view(), name='basket-vouchers-add'),    
    url(r'^saved/$', SavedView.as_view(), name='basket-saved'),
)