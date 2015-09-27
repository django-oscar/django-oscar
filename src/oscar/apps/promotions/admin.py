from django.contrib import admin

from oscar.apps.promotions.models import (
    AutomaticProductList, HandPickedProductList, Image,
    KeywordPromotion, MultiImage, OrderedProduct, PagePromotion,
    RawHTML, SingleProduct, TabbedBlock)


class OrderProductInline(admin.TabularInline):
    model = OrderedProduct


class HandPickedProductListAdmin(admin.ModelAdmin):
    inlines = [OrderProductInline]


class PagePromotionAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'content_object', 'position']
    exclude = ['clicks']


class KeywordPromotionAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'position', 'clicks']
    readonly_fields = ['clicks']


admin.site.register(Image)
admin.site.register(MultiImage)
admin.site.register(RawHTML)
admin.site.register(HandPickedProductList, HandPickedProductListAdmin)
admin.site.register(AutomaticProductList)
admin.site.register(TabbedBlock)
admin.site.register(PagePromotion, PagePromotionAdmin)
admin.site.register(KeywordPromotion, KeywordPromotionAdmin)
admin.site.register(SingleProduct)
