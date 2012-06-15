from django.contrib import admin
from django.db.models import get_model
from treebeard.admin import TreeAdmin

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
Option = get_model('catalogue', 'Option')
ProductRecommendation = get_model('catalogue', 'ProductRecommendation')
AttributeOption = get_model('catalogue', 'AttributeOption')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeEntity = get_model('catalogue', 'AttributeEntity')
AttributeEntityType = get_model('catalogue', 'AttributeEntityType')
ProductImage = get_model('catalogue', 'ProductImage')
Category = get_model('catalogue', 'Category')
ProductCategory = get_model('catalogue', 'ProductCategory')


class AttributeInline(admin.TabularInline):
    model = ProductAttributeValue

class ProductRecommendationInline(admin.TabularInline):
    model = ProductRecommendation
    fk_name = 'primary'
    
class CategoryInline(admin.TabularInline):
    model = ProductCategory
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
    model = AttributeOption
    
class AttributeOptionGroupAdmin(admin.ModelAdmin):
    inlines = [AttributeOptionInline, ]
        
class AttributeEntityAdmin(admin.ModelAdmin):
    list_display = ('name', )
                 
class CategoryAdmin(TreeAdmin):
    pass

admin.site.register(ProductClass, ProductClassAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(AttributeEntity, AttributeEntityAdmin)
admin.site.register(AttributeEntityType)
admin.site.register(Option, OptionAdmin)
admin.site.register(ProductImage)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductCategory)
