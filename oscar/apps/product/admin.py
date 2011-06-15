from django.contrib import admin

from oscar.core.loading import import_module
product_models = import_module('product.models', ['Item', 'ItemClass', 'AttributeType', 'AttributeValueOption',
                                                  'ItemAttributeValue', 'Option', 'ProductRecommendation', 
                                                  'ProductImage', 'Category', 'ItemCategory'])

class AttributeInline(admin.TabularInline):
    model = product_models.ItemAttributeValue

class ProductRecommendationInline(admin.TabularInline):
    model = product_models.ProductRecommendation
    fk_name = 'primary'
    
class CategoryInline(admin.TabularInline):
    model = product_models.ItemCategory
    extra = 1

class ItemClassAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    
class ItemAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'upc', 'get_item_class', 'is_top_level', 'is_group', 'is_variant', 'attribute_summary', 'date_created')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [AttributeInline, CategoryInline, ProductRecommendationInline]
    
class AttributeTypeAdmin(admin.ModelAdmin):
    exclude = ['code']
    
class OptionAdmin(admin.ModelAdmin):
    exclude = ['code']

admin.site.register(product_models.ItemClass, ItemClassAdmin)
admin.site.register(product_models.Item, ItemAdmin)
admin.site.register(product_models.AttributeType, AttributeTypeAdmin)
admin.site.register(product_models.ItemAttributeValue)
admin.site.register(product_models.Option, OptionAdmin)
admin.site.register(product_models.ProductImage)
admin.site.register(product_models.Category)
admin.site.register(product_models.AttributeValueOption)
