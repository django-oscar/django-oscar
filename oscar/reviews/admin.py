from django.contrib import admin

from oscar.reviews.models import ProductReview, Vote


class ProductReviewAdmin(admin.ModelAdmin):    
    list_display = ('title', 'score', 'approved', 'date_created', 'up_votes', 'down_votes')
    read_only = ('title', 'body', 'score', 'up_votes', 'down_votes')

    
class VoteAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'up', 'down', 'date_created')
    read_only = ('review', 'user', 'up', 'down', 'date_created')
    
admin.site.register(ProductReview, ProductReviewAdmin) 
admin.site.register(Vote, VoteAdmin)
