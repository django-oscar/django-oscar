"""
Serializers used by the mobile app (Flutter).

Unlike the default oscarapi product serializers, price and availability are
inlined so a product list is a single request.
"""
from rest_framework import serializers

from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class, get_api_classes

Category = get_model("catalogue", "Category")
Product = get_model("catalogue", "Product")

(
    CategorySerializer,
    ProductImageSerializer,
    AvailabilitySerializer,
) = get_api_classes(
    "serializers.product",
    ["CategorySerializer", "ProductImageSerializer", "AvailabilitySerializer"],
)
PriceSerializer = get_api_class("serializers.checkout", "PriceSerializer")


class MobileCategorySerializer(CategorySerializer):
    id = serializers.IntegerField(read_only=True)
    parent_id = serializers.SerializerMethodField()
    has_children = serializers.SerializerMethodField()

    def get_parent_id(self, obj):
        if obj.is_root():
            return None
        parent_path = obj.path[: -obj.steplen]
        return (
            Category.objects.filter(path=parent_path)
            .values_list("pk", flat=True)
            .first()
        )

    def get_has_children(self, obj):
        return obj.numchild > 0


class MobileProductCategorySerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    id = serializers.IntegerField()
    name = serializers.CharField()


class MobileProductSerializer(serializers.ModelSerializer):
    """
    Expects a purchase ``strategy`` in the serializer context, see
    apps.api.views.product.MobileStrategyMixin.
    """

    images = ProductImageSerializer(many=True, read_only=True)
    categories = MobileProductCategorySerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "upc",
            "title",
            "description",
            "structure",
            "rating",
            "images",
            "categories",
            "price",
            "availability",
        )

    def _purchase_info(self, obj):
        return self.context["strategy"].fetch_for_product(obj)

    def get_price(self, obj):
        return PriceSerializer(self._purchase_info(obj).price, context=self.context).data

    def get_availability(self, obj):
        return AvailabilitySerializer(
            self._purchase_info(obj).availability, context=self.context
        ).data
