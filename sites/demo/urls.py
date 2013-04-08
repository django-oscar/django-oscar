from django.conf.urls import patterns, include
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from stores.app import application as stores_app
from stores.dashboard.app import application as dashboard_app

from apps.app import application

# These need to be imported into this namespace
from oscar.views import handler500, handler404, handler403

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    # Stores extension
    (r'^stores/', include(stores_app.urls)),
    (r'^dashboard/stores/', include(dashboard_app.urls)),

    (r'', include(application.urls)),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
