from django.conf.urls import patterns, include
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from stores.app import application as stores_app
from stores.dashboard.app import application as dashboard_app

from apps.app import application
from datacash.app import application as datacash_app

# These need to be imported into this namespace
from oscar.views import handler500, handler404, handler403

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    # Stores extension
    (r'^stores/', include(stores_app.urls)),
    (r'^dashboard/stores/', include(dashboard_app.urls)),

    # PayPal extension
    (r'^checkout/paypal/', include('paypal.express.urls')),

    # Datacash extension
    (r'^dashboard/datacash/', include(datacash_app.urls)),

    (r'', include(application.urls)),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
