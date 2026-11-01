"""
Mobile endpoints that django-oscar-api does not provide, mounted under /api/
before oscarapi.urls (see sandbox/urls.py).
"""
from django.urls import path

from apps.api.views.review import MyReviewList, ProductReviewList

urlpatterns = [
    path(
        "products/<int:pk>/reviews/",
        ProductReviewList.as_view(),
        name="api-product-reviews",
    ),
    path("reviews/mine/", MyReviewList.as_view(), name="api-my-reviews"),
]
