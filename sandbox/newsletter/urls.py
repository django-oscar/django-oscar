from django.urls import path

from .views import SubscriberViewSet

urlpatterns = [
    path('subscribe', SubscriberViewSet.as_view({'post': 'create'}), name='subscribe'),
]