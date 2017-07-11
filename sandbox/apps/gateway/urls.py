from django.conf.urls import url

from apps.gateway import views

urlpatterns = [
    url(r'^$', views.GatewayView.as_view(), name='gateway')
]
