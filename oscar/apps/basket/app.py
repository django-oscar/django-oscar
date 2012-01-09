from django.conf.urls.defaults import patterns, url

from oscar.apps.basket.views import (BasketView, SavedView,
    VoucherAddView, BasketAddView, VoucherRemoveView)
from oscar.core.application import Application


class BasketApplication(Application):
    name = 'basket'
    summary_view = BasketView
    saved_view = SavedView
    add_view = BasketAddView
    add_voucher_view = VoucherAddView
    remove_voucher_view = VoucherRemoveView

    def get_urls(self):
        urlpatterns = patterns('',                   
            url(r'^$', self.summary_view.as_view(), name='summary'),
            url(r'^add/$', self.add_view.as_view(), name='add'),    
            url(r'^vouchers/add/$', self.add_voucher_view.as_view(), name='vouchers-add'),
            url(r'^vouchers/(?P<pk>\d+)/remove/$', self.remove_voucher_view.as_view(), name='vouchers-remove'),     
            url(r'^saved/$', self.saved_view.as_view(), name='saved'),
        )
        return self.post_process_urls(urlpatterns)

application = BasketApplication()