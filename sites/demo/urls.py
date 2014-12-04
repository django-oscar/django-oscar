from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from stores.app import application as stores_app
from stores.dashboard.app import application as dashboard_app

from apps.app import application
from datacash.dashboard.app import application as datacash_app

# These need to be imported into this namespace
from oscar.views import handler500, handler404, handler403  # noqa

js_info_dict = {
    'packages': ('stores',),
}

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),

    # Stores extension
    url(r'^stores/', include(stores_app.urls)),
    url(r'^dashboard/stores/', include(dashboard_app.urls)),

    # PayPal extension
    url(r'^checkout/paypal/', include('paypal.express.urls')),

    # Datacash extension
    url(r'^dashboard/datacash/', include(datacash_app.urls)),

    url(r'', include(application.urls)),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
