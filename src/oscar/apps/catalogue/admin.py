from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

AttributeOption = get_model('catalogue', 'AttributeOption')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
Category = get_model('catalogue', 'Category')
Option = get_model('catalogue', 'Option')
Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductClass = get_model('catalogue', 'ProductClass')
ProductImage = get_model('catalogue', 'ProductImage')
ProductRecommendation = get_model('catalogue', 'ProductRecommendation')


class AttributeInline(admin.TabularInline):
    model = ProductAttributeValue


class ProductRecommendationInline(admin.TabularInline):
    model = ProductRecommendation
    fk_name = 'primary'
    raw_id_fields = ['primary', 'recommendation']


class CategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 2


class ProductClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'requires_shipping', 'track_stock')
    inlines = [ProductAttributeInline]


class ProductAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    list_display = ('get_title', 'upc', 'get_product_class', 'structure',
                    'attribute_summary', 'date_created')
    list_filter = ['structure', 'is_discountable']
    raw_id_fields = ['parent']
    inlines = [AttributeInline, CategoryInline, ProductRecommendationInline]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ['upc', 'title']

    def get_queryset(self, request):
        qs = super(ProductAdmin, self).get_queryset(request)
        return (
            qs
            .select_related('product_class', 'parent')
            .prefetch_related(
                'attribute_values',
                'attribute_values__attribute'))


class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'product_class', 'type')
    prepopulated_fields = {"code": ("name", )}


class OptionAdmin(admin.ModelAdmin):
    pass


class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value')


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'option_summary')
    inlines = [AttributeOptionInline, ]


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display = ('name', 'slug')


admin.site.register(ProductClass, ProductClassAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(ProductImage)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductCategory)
