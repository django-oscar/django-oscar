from django.conf.urls import include, url

from .views import BandCreateView, BandDeleteView, BandListView, BandUpdateView

dashboard_urlpatterns = [
    url(r'^band/create/$', BandCreateView.as_view(), name='oscar-band-create'),
    url(r'^band/$', BandListView.as_view(), name='oscar-band-list'),
    # The RelatedFieldWidgetWrapper code does something funny with placeholder
    # urls, so it does need to match more than just a pk
    url(r'^band/(?P<pk>\w+)/update/$', BandUpdateView.as_view(), name='oscar-band-update'),
    # The RelatedFieldWidgetWrapper code does something funny with placeholder
    # urls, so it does need to match more than just a pk
    url(r'^band/(?P<pk>\w+)/delete/$', BandDeleteView.as_view(), name='oscar-band-delete'),
]

urlpatterns = [
    url(r'^dashboard/', include((dashboard_urlpatterns, 'dashboard'), namespace='dashboard')),
]
