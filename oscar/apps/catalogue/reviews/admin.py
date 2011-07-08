from django.contrib import admin

from oscar.apps.catalogue.reviews.models import ProductReview, Vote


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'score', 'status', 'total_votes', 'delta_votes', 'date_created')
    readonly_fields = ('total_votes', 'delta_votes')


class VoteAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'delta', 'date_created')

admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Vote, VoteAdmin)
