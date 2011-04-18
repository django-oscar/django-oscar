from django.contrib import admin

from oscar.reviews.models import ProductReview, Vote

class ProductReviewAdmin(admin.ModelAdmin):    
    list_display = ('title', 'score', 'approved')
    read_only = ('title', 'body', 'score')
    
class VoteAdmin(admin.ModelAdmin):
    #list_display = ('')
    pass
    
admin.site.register(ProductReview, ProductReviewAdmin) 
admin.site.register(Vote, VoteAdmin)