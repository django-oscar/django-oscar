from django.conf.urls.defaults import patterns, url
from oscar.apps.basket.views import BasketView, SavedView, VoucherView, VoucherAddView, BasketAddView
from oscar.core.application import Application

class BasketApplication(Application):
    name = 'basket'
    summary_view = BasketView
    saved_view = SavedView
    voucher_view = VoucherView
    add_view = BasketAddView
    add_voucher_view = VoucherAddView

    def get_urls(self):
        urlpatterns = patterns('',                   
            url(r'^$', self.summary_view.as_view(), name='summary'),
            url(r'^add/$', self.add_view.as_view(), name='add'),    
            url(r'^vouchers/$', self.voucher_view.as_view(), name='vouchers'),
            url(r'^vouchers/add/$', self.add_voucher_view.as_view(), name='vouchers-add'),    
            url(r'^saved/$', self.saved_view.as_view(), name='saved'),
        )
        return urlpatterns

application = BasketApplication()