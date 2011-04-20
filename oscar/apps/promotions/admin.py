from django.contrib import admin

from oscar.core.loading import import_module
models = import_module('promotions.models', ['Promotion', 'PagePromotion', 'KeywordPromotion'])

class PromotionAdmin(admin.ModelAdmin):
    pass

class PagePromotionAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'position', 'clicks']
    readonly_fields = ['clicks']

class KeywordPromotionAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'position', 'clicks']
    readonly_fields = ['clicks']

admin.site.register(models.Promotion, PromotionAdmin)
admin.site.register(models.PagePromotion, PagePromotionAdmin)
admin.site.register(models.KeywordPromotion, KeywordPromotionAdmin)
