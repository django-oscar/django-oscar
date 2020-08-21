from django.urls import include, path

from .views import BandCreateView, BandDeleteView, BandListView, BandUpdateView

dashboard_urlpatterns = [
    path('band/create/', BandCreateView.as_view(), name='oscar-band-create'),
    path('band/', BandListView.as_view(), name='oscar-band-list'),
    # The RelatedFieldWidgetWrapper code does something funny with placeholder
    # urls, so it does need to match more than just a pk
    path('band/<str:pk>/update/', BandUpdateView.as_view(), name='oscar-band-update'),
    # The RelatedFieldWidgetWrapper code does something funny with placeholder
    # urls, so it does need to match more than just a pk
    path('band/<str:pk>/delete/', BandDeleteView.as_view(), name='oscar-band-delete'),
]

urlpatterns = [
    path('dashboard/', include((dashboard_urlpatterns, 'dashboard'), namespace='dashboard')),
]
