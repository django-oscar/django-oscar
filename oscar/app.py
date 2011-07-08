from django.conf.urls.defaults import patterns, url, include

from oscar.core.application import Application
from oscar.apps.catalogue.app import application as product_app
from oscar.apps.customer.app import application as customer_app
from oscar.apps.basket.app import application as basket_app
from oscar.apps.checkout.app import application as checkout_app
from oscar.apps.promotions.app import application as promotions_app
from oscar.apps.order_management.app import application as order_management_app
from oscar.apps.search.app import application as search_app
from oscar.apps.reports.app import application as reports_app


class Shop(Application):
    name = None
    
    product_app = product_app
    customer_app = customer_app
    basket_app = basket_app
    checkout_app = checkout_app
    promotions_app = promotions_app
    order_management_app = order_management_app
    search_app = search_app
    reports_app = reports_app
    
    def get_urls(self):
        urlpatterns = patterns('',
            (r'products/', include(self.product_app.urls)),
            (r'basket/', include(self.basket_app.urls)),
            (r'checkout/', include(self.checkout_app.urls)),
            (r'order-management/', include(self.order_management_app.urls)),
            (r'accounts/', include(self.customer_app.urls)),
            (r'reports/', include(self.reports_app.urls)),
            (r'search/', include(self.search_app.urls)),
            (r'', include(self.promotions_app.urls)),             
        )
        return urlpatterns
    
shop = Shop()