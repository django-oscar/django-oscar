from django.apps import apps
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from tests._site.apps.myapp.views import TestView

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("app:shop/", include(apps.get_app_config("oscar").urls[0])),
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("test/", TestView),
)

urlpatterns += staticfiles_urlpatterns()

handler403 = "oscar.views.handler403"
handler404 = "oscar.views.handler404"
handler500 = "oscar.views.handler500"
