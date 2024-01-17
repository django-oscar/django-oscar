from django.urls import path
from .views import BlogListCreateAPIView, BlogDetailAPIView

urlpatterns = [
    path('blogs/', BlogListCreateAPIView.as_view(), name='blog-list'),
    path('blogs/<int:pk>/', BlogDetailAPIView.as_view(), name='blog-detail'),
]