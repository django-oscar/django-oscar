from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

AttributeOption = get_model("catalogue", "AttributeOption")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Category = get_model("catalogue", "Category")
Option = get_model("catalogue", "Option")
Product = get_model("catalogue", "Product")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductClass = get_model("catalogue", "ProductClass")
ProductImage = get_model("catalogue", "ProductImage")
ProductRecommendation = get_model("catalogue", "ProductRecommendation")


class AttributeInline(admin.TabularInline):
    model = ProductAttributeValue
    raw_id_fields = ("attribute",)


class ProductRecommendationInline(admin.TabularInline):
    model = ProductRecommendation
    fk_name = "primary"
    raw_id_fields = ["primary", "recommendation"]


class CategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    autocomplete_fields = ("category",)


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 2


class ProductClassAdmin(admin.ModelAdmin):
    list_display = ("name", "requires_shipping", "track_stock")
    inlines = [ProductAttributeInline]
    search_fields = ("name", "slug")


class ProductAdmin(admin.ModelAdmin):
    date_hierarchy = "date_created"
    list_display = (
        "get_title",
        "upc",
        "get_product_class",
        "structure",
        "attribute_summary",
        "date_created",
    )
    list_filter = ["structure", "is_discountable", "is_public"]
    raw_id_fields = ["parent"]
    inlines = [AttributeInline, CategoryInline, ProductRecommendationInline]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["upc", "title"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("product_class", "parent").prefetch_related(
            "attribute_values", "attribute_values__attribute"
        )


class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "product_class", "type")
    prepopulated_fields = {"code": ("name",)}
    search_fields = ("name", "code", "product_class__name")
    autocomplete_fields = ("option_group",)


class OptionAdmin(admin.ModelAdmin):
    autocomplete_fields = ("option_group",)
    search_fields = ("name", "option_group__name")
    list_filter = ("type",)
    list_display = ("name", "type")


class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("product", "attribute", "value")
    autocomplete_fields = ("product",)
    raw_id_fields = ("attribute",)


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "option_summary")
    inlines = [
        AttributeOptionInline,
    ]
    search_fields = ("name",)


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_filter = ["is_public"]
    list_display = ("name", "slug")
    search_fields = ("name", "slug", "pk")


class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("pk", "product", "category")
    search_fields = (
        "product__upc",
        "product__title",
        "product__slug",
        "category__name",
        "category__slug",
    )
    autocomplete_fields = ("product", "category")


class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "caption")
    search_fields = ("caption", "product__upc", "product__title")
    autocomplete_fields = ("product",)


admin.site.register(ProductClass, ProductClassAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
