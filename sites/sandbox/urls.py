from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static

from oscar.app import shop

# These simply need to be imported into this namespace.  Ignore the PEP8
# warning that they aren't used.
from oscar.views import handler500, handler404, handler403

admin.autodiscover()

urlpatterns = patterns('',
    # Include admin as convenience. It's unsupported and you should
    # use the dashboard
    (r'^admin/', include(admin.site.urls)),
    # Custom functionality to allow dashboard users to be created
    (r'^gateway/', include('apps.gateway.urls')),
    (r'', include(shop.urls)),
)

# Allow rosetta to be used to add translations
if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^rosetta/', include('rosetta.urls')),
    )

if settings.DEBUG:
    import debug_toolbar

    # Server statics and uploaded media
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    # Allow error pages to be tested
    urlpatterns += patterns('',
        url(r'^403$', handler403),
        url(r'^404$', handler404),
        url(r'^500$', handler500)
    )
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
