"""
Product reviews for the mobile app (not provided by django-oscar-api).
Routed in apps/api/urls.py.
"""
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_model
from rest_framework import generics, permissions, serializers

from apps.api.mobile_serializers import MobileReviewSerializer

Product = get_model("catalogue", "Product")
ProductReview = get_model("reviews", "ProductReview")


class ProductReviewList(generics.ListCreateAPIView):
    """
    GET: approved reviews of a product, newest first (public).
    POST: review the product as the signed-in user (one review per product).
    The review is approved at once unless OSCAR_MODERATE_REVIEWS is on.
    """

    serializer_class = MobileReviewSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_product(self):
        return get_object_or_404(Product.objects.browsable(), pk=self.kwargs["pk"])

    def get_queryset(self):
        return (
            self.get_product()
            .reviews.approved()
            .select_related("user", "product")
            .order_by("-date_created", "-id")
        )

    def perform_create(self, serializer):
        product = self.get_product()
        if not product.is_review_permitted(self.request.user):
            raise serializers.ValidationError(
                {"non_field_errors": [_("You have already reviewed this product.")]}
            )
        serializer.save(product=product, user=self.request.user)


class MyReviewList(generics.ListAPIView):
    """Reviews written by the signed-in user, whatever their status"""

    serializer_class = MobileReviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            ProductReview.objects.filter(user=self.request.user)
            .select_related("user", "product")
            .order_by("-date_created", "-id")
        )
