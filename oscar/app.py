from django.conf.urls.defaults import patterns, url, include
from oscar.core.application import Application
from oscar.apps.product import application as product_app
from oscar.apps.customer import application as customer_app


class Shop(Application):
    name = None
    product_app = product_app
    customer_app = customer_app
    
    def get_urls(self):
        urlpatterns = patterns('',
            (r'products/', include(self.product_app.urls)),
            (r'basket/', include('oscar.apps.basket.urls')),
            (r'checkout/', include('oscar.apps.checkout.urls')),
            (r'order-management/', include('oscar.apps.order_management.urls')),
            (r'accounts/', include(self.customer_app.urls)),
            (r'promotions/', include('oscar.apps.promotions.urls')),
            (r'reports/', include('oscar.apps.reports.urls')),
            (r'search/', include('oscar.apps.search.urls')),
            (r'^$', include('oscar.apps.promotions.urls')),             
        )
        return urlpatterns
    
shop = Shop()