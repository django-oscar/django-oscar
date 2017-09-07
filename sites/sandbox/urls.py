from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

from oscar.app import shop

from apps.sitemaps import base_sitemaps


admin.autodiscover()

urlpatterns = [
    # Include admin as convenience. It's unsupported and you should
    # use the dashboard
    url(r'^admin/', include(admin.site.urls)),
    # i18n URLS need to live outside of i18n_patterns scope of the shop
    url(r'^i18n/', include('django.conf.urls.i18n')),
    # include a basic sitemap
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.index', {
        'sitemaps': base_sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$',
        'django.contrib.sitemaps.views.sitemap', {'sitemaps': base_sitemaps}),
]

# Prefix Oscar URLs with language codes
urlpatterns += i18n_patterns('',
    # Custom functionality to allow dashboard users to be created
    url(r'gateway/', include('apps.gateway.urls')),
    # Oscar's normal URLs
    url(r'', include(shop.urls)),
)
