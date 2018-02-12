from django.conf.urls import url

from oscar.apps.catalogue import app

from .views import ParentProductDetailView


class CatalogueApplication(app.CatalogueApplication):
    def get_urls(self):
        urlpatterns = super(CatalogueApplication, self).get_urls()
        urlpatterns += [
            url(r'^parent/(?P<product_slug>[\w-]*)_(?P<pk>\d+)/$', ParentProductDetailView.as_view(),
                name='parent_detail')]
        return self.post_process_urls(urlpatterns)


application = CatalogueApplication()
