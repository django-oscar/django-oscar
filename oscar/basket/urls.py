from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.basket.views',
    url(r'add-item$', 'add', name='oscar-basket-add'),
)
