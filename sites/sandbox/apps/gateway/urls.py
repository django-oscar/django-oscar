from django.conf.urls import patterns, url

from apps.gateway import views

urlpatterns = patterns('',
    url(r'^$', views.GatewayView.as_view(), name='gateway')
)
