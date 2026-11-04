"""
Favorites of the mobile app, stored in the Oscar wish list the website uses
(the first wish list of the user, created on the first addition like
``customer.wishlists.views.WishListAddProduct``). Routed in apps/api/urls.py.
"""
from django.shortcuts import get_object_or_404
from oscar.core.loading import get_class, get_model
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.mobile_serializers import MobileProductSerializer
from apps.api.views.product import with_reviews_count

Selector = get_class("partner.strategy", "Selector")
Product = get_model("catalogue", "Product")


def default_wishlist(user, create=False):
    wishlist = user.wishlists.all().first()
    if wishlist is None and create:
        wishlist = user.wishlists.create()
    return wishlist


def browsable_products():
    return with_reviews_count(Product.objects.browsable()).prefetch_related(
        "images", "categories", "stockrecords"
    )


class WishlistAddSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    product = serializers.IntegerField()


class WishlistView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def serialize(self, products, many=False):
        request = self.request
        context = {
            "request": request,
            "strategy": Selector().strategy(request=request, user=request.user),
        }
        return MobileProductSerializer(products, many=many, context=context).data


class Wishlist(WishlistView):
    """
    GET: browsable products of the wish list, last added first.
    POST: add ``product`` (201, or 200 when it was already there).
    """

    def get(self, request):
        wishlist = default_wishlist(request.user)
        if wishlist is None:
            return Response([])
        product_ids = list(
            wishlist.lines.filter(product__isnull=False)
            .order_by("-id")
            .values_list("product_id", flat=True)
        )
        products = browsable_products().in_bulk(product_ids)
        return Response(
            self.serialize(
                [products[pk] for pk in product_ids if pk in products], many=True
            )
        )

    def post(self, request):
        data = WishlistAddSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        product = get_object_or_404(
            browsable_products(), pk=data.validated_data["product"]
        )
        wishlist = default_wishlist(request.user, create=True)
        created = not wishlist.lines.filter(product=product).exists()
        if created:
            wishlist.add(product)
        return Response(
            self.serialize(product),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WishlistItem(WishlistView):
    """DELETE: remove the product from the wish list (204, also when absent)"""

    def delete(self, request, product_id):
        wishlist = default_wishlist(request.user)
        if wishlist is not None:
            wishlist.lines.filter(product_id=product_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
