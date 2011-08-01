from django.contrib import admin

from oscar.core.loading import import_module
product_models = import_module('catalogue.models', ['Product', 'ProductClass', 'ProductAttribute', 'ProductAttributeValue', 
                                                    'Option', 'ProductRecommendation', 'AttributeOption', 'AttributeOptionGroup',
                                                    'AttributeEntity', 'AttributeEntityType', 'ProductImage', 'Category', 
                                                    'ProductCategory'])

class AttributeInline(admin.TabularInline):
    model = product_models.ProductAttributeValue

class ProductRecommendationInline(admin.TabularInline):
    model = product_models.ProductRecommendation
    fk_name = 'primary'
    
class CategoryInline(admin.TabularInline):
    model = product_models.ProductCategory
    extra = 1

class ProductClassAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    
class ProductAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'upc', 'get_product_class', 'is_top_level', 'is_group', 'is_variant', 'attribute_summary', 'date_created')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [AttributeInline, CategoryInline, ProductRecommendationInline]
    
class ProductAttributeAdmin(admin.ModelAdmin):
    prepopulated_fields = {"code": ("name", )}
    
class OptionAdmin(admin.ModelAdmin):
    exclude = ['code']
    
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value')

class AttributeOptionInline(admin.TabularInline):
    model = product_models.AttributeOption
    
class AttributeOptionGroupAdmin(admin.ModelAdmin):
    inlines = [AttributeOptionInline, ]
        
class AttributeEntityAdmin(admin.ModelAdmin):
    list_display = ('name', )
                 

admin.site.register(product_models.ProductClass, ProductClassAdmin)
admin.site.register(product_models.Product, ProductAdmin)
admin.site.register(product_models.ProductAttribute, ProductAttributeAdmin)
admin.site.register(product_models.ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(product_models.AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(product_models.AttributeEntity, AttributeEntityAdmin)
admin.site.register(product_models.AttributeEntityType)
admin.site.register(product_models.Option, OptionAdmin)
admin.site.register(product_models.ProductImage)
admin.site.register(product_models.Category)
