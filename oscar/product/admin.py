from django.contrib import admin

from oscar.services import import_module
product_models = import_module('product.models', ['Item', 'ItemClass', 'AttributeType', 
                                                  'ItemAttributeValue', 'Option'])

class AttributeInline(admin.TabularInline):
    model = product_models.ItemAttributeValue

class ItemClassAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    
class ItemAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'upc', 'get_item_class', 'is_top_level', 'is_group', 'is_variant', 'attribute_summary', 'date_created')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [AttributeInline]
    
class AttributeTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {"code": ("name",)}

admin.site.register(product_models.ItemClass, ItemClassAdmin)
admin.site.register(product_models.Item, ItemAdmin)
admin.site.register(product_models.AttributeType, AttributeTypeAdmin)
admin.site.register(product_models.ItemAttributeValue)
admin.site.register(product_models.Option)
