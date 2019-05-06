from django.apps import apps
from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from tests._site.apps.myapp.views import TestView

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include(apps.get_app_config('oscar').urls[0])),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    url(r'test/', TestView),
)

urlpatterns += staticfiles_urlpatterns()

handler403 = 'oscar.views.handler403'
handler404 = 'oscar.views.handler404'
handler500 = 'oscar.views.handler500'
