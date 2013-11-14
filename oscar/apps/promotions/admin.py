from django.contrib import admin

from oscar.apps.promotions.models import Image, MultiImage, RawHTML, HandPickedProductList, OrderedProduct, AutomaticProductList, TabbedBlock, \
                                  PagePromotion, KeywordPromotion, SingleProduct


class OrderProductInline(admin.TabularInline):
    model = OrderedProduct
    
class HandPickedProductListAdmin(admin.ModelAdmin):
    inlines = [OrderProductInline]

class PagePromotionAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'content_object', 'position']
    exclude = ['clicks']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(PagePromotionAdmin,self).get_form(request, obj, **kwargs)
        # Only allow links to models within the promotions app
        form.base_fields['content_type'].queryset = form.base_fields['content_type'].queryset.filter(app_label='promotions')
        return form

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


