from django.contrib import admin

from oscar.apps.reviews.models import ProductReview, Vote


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'score', 'approved', 'date_created', 'total_votes', 'delta_votes')
    read_only = ('title', 'body', 'score', 'total_votes', 'delta_votes')


class VoteAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'choice', 'date_created')
    read_only = ('review', 'user', 'choice', 'date_created')

admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Vote, VoteAdmin)
