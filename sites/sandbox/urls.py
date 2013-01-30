from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.views.generic import TemplateView

from oscar.app import shop
from oscar.views import handler500, handler404, handler403

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^gateway/', include('apps.gateway.urls')),
    (r'', include(shop.urls)),
)

# Allow rosetta to be used to add translations
if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^rosetta/', include('rosetta.urls')),
    )

if settings.DEBUG:
    # Server statics
    urlpatterns += staticfiles_urlpatterns()
    # Serve uploaded media
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    # Test error pages
    urlpatterns += patterns('',
        url(r'^403$', TemplateView.as_view(template_name='403.html')),
        url(r'^404$', TemplateView.as_view(template_name='404.html')),
        url(r'^500$', TemplateView.as_view(template_name='500.html')),
    )
