from django.contrib import admin

from oscar.apps.promotions.models import Banner, Pod, HandPickedProductList, OrderedProduct, AutomaticProductList, TabbedBlock, \
                                  PagePromotion, KeywordPromotion


class OrderProductInline(admin.TabularInline):
    model = OrderedProduct
    
class HandPickedProductListAdmin(admin.ModelAdmin):
    inlines = [OrderProductInline]

class PagePromotionAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'position', 'clicks']
    readonly_fields = ['clicks']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(PagePromotionAdmin,self).get_form(request, obj, **kwargs)
        form.base_fields['content_type'].queryset = form.base_fields['content_type'].queryset.filter(app_label='promotions')
        return form

class KeywordPromotionAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'position', 'clicks']
    readonly_fields = ['clicks']


admin.site.register(Banner)
admin.site.register(Pod)
admin.site.register(HandPickedProductList, HandPickedProductListAdmin)
admin.site.register(AutomaticProductList)
admin.site.register(TabbedBlock)
admin.site.register(PagePromotion, PagePromotionAdmin)
admin.site.register(KeywordPromotion, KeywordPromotionAdmin)


