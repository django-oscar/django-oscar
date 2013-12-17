from django.db import models


class ApprovedReviewsManager(models.Manager):
    def get_query_set(self):
        queryset = super(ApprovedReviewsManager, self).get_query_set()
        return queryset.filter(status=1)


class RecentReviewsManager(models.Manager):
    def get_query_set(self):
        queryset = super(RecentReviewsManager, self).get_query_set()
        return queryset.filter(approved=True).order_by('-date_created')


class TopScoredReviewsManager(models.Manager):
    def get_query_set(self):
        queryset = super(TopScoredReviewsManager, self).get_query_set()
        return queryset.filter(approved=True).order_by('-score')


class TopVotedReviewsManager(models.Manager):
    def get_query_set(self):
        queryset = super(TopVotedReviewsManager, self).get_query_set()
        return queryset.filter(approved=True).order_by('-delta_votes')
