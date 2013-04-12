from django.contrib import admin
from django.db.models import get_model, Q
from treebeard.admin import TreeAdmin
from ajax_select import LookupChannel, make_ajax_form

AttributeEntity = get_model('catalogue', 'AttributeEntity')
AttributeEntityType = get_model('catalogue', 'AttributeEntityType')
AttributeOption = get_model('catalogue', 'AttributeOption')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
Category = get_model('catalogue', 'Category')
ContributorRole = get_model('catalogue', 'ContributorRole')
Contributor = get_model('catalogue', 'Contributor')
Option = get_model('catalogue', 'Option')
Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductClass = get_model('catalogue', 'ProductClass')
ProductImage = get_model('catalogue', 'ProductImage')
ProductRecommendation = get_model('catalogue', 'ProductRecommendation')


class ProductLookup(LookupChannel):
    """Ajax lookup for product fields using django-ajax-selects"""
    model = Product

    def get_query(self, q, request):
        qs = (Product.objects.select_related('parent')
                             .order_by('title', 'parent__title'))
        qs = qs.filter(Q(title__icontains=q) | Q(parent__title__icontains=q))
        qs = qs[:15] # Big numbers don't look well and extend long below page
                     # we could updated css and add `overflow: scroll`
                     # to the selection box
        return qs


class AttributeInline(admin.TabularInline):
    model = ProductAttributeValue


class ProductRecommendationInline(admin.TabularInline):
    model = ProductRecommendation
    fk_name = 'primary'
    form = make_ajax_form(ProductRecommendation, {'recommendation': 'product'},
                          show_help_text=True)


class CategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1


class ProductClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'requires_shipping', 'track_stock')
    prepopulated_fields = {"slug": ("name",)}


class ContributorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


class ContributorRoleAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


class ProductAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'upc', 'get_product_class', 'is_top_level',
                    'is_group', 'is_variant', 'attribute_summary',
                    'date_created')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [AttributeInline, CategoryInline, ProductRecommendationInline]
    form = make_ajax_form(Product, {'parent': 'product',
                                    'related_products': 'product',})


class ProductAttributeAdmin(admin.ModelAdmin):
    prepopulated_fields = {"code": ("name", )}


class OptionAdmin(admin.ModelAdmin):
    exclude = ['code']


class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value')


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    inlines = [AttributeOptionInline, ]


class AttributeEntityAdmin(admin.ModelAdmin):
    list_display = ('name', )


class CategoryAdmin(TreeAdmin):
    pass


admin.site.register(ProductClass, ProductClassAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ContributorRole, ContributorRoleAdmin)
admin.site.register(Contributor, ContributorAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(AttributeEntity, AttributeEntityAdmin)
admin.site.register(AttributeEntityType)
admin.site.register(Option, OptionAdmin)
admin.site.register(ProductImage)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductCategory)
