from django.conf.urls.defaults import patterns, url, include

from oscar.core.application import Application
from oscar.apps.product.app import application as product_app
from oscar.apps.customer.app import application as customer_app
from oscar.apps.basket.app import application as basket_app
from oscar.apps.checkout.app import application as checkout_app
from oscar.apps.promotions.app import application as promotions_app


class Shop(Application):
    name = None
    product_app = product_app
    customer_app = customer_app
    basket_app = basket_app
    checkout_app = checkout_app
    promotions_app = promotions_app
    
    def get_urls(self):
        urlpatterns = patterns('',
            (r'products/', include(self.product_app.urls)),
            (r'basket/', include(self.basket_app.urls)),
            (r'checkout/', include(self.checkout_app.urls)),
            (r'order-management/', include('oscar.apps.order_management.urls')),
            (r'accounts/', include(self.customer_app.urls)),
            (r'reports/', include('oscar.apps.reports.urls')),
            (r'search/', include('oscar.apps.search.urls')),
            (r'^$', include(self.promotions_app.urls)),             
        )
        return urlpatterns
    
shop = Shop()