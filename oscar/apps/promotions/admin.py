from django.contrib import admin

from oscar.core.loading import import_module
import_module('promotions.models', ['Promotion', 'PagePromotion', 'KeywordPromotion',
                                    'MerchandisingBlock', 'PageMerchandisingBlock', 'KeywordMerchandisingBlock',
                                    'MerchandisingBlockProduct'], locals())

class PromotionAdmin(admin.ModelAdmin):
    pass

class PagePromotionAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'position', 'clicks']
    readonly_fields = ['clicks']

class KeywordPromotionAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'position', 'clicks']
    readonly_fields = ['clicks']
  
class MerchandisingBlockProductline(admin.TabularInline):
    model = MerchandisingBlockProduct
    raw_id_fields = ("product",)
    extra = 1    
    
class MerchandisingBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'num_products']
    inlines = (MerchandisingBlockProductline,)
    
class PageMerchandisingBlockAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'block', 'display_order']

admin.site.register(Promotion, PromotionAdmin)
admin.site.register(PagePromotion, PagePromotionAdmin)
admin.site.register(KeywordPromotion, KeywordPromotionAdmin)

admin.site.register(MerchandisingBlock, MerchandisingBlockAdmin)
admin.site.register(PageMerchandisingBlock, PageMerchandisingBlockAdmin)
admin.site.register(KeywordMerchandisingBlock)


