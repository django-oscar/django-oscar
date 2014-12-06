from django.db import models


class ApprovedReviewsManager(models.Manager):
    def get_queryset(self):
        queryset = super(ApprovedReviewsManager, self).get_queryset()
        return queryset.filter(status=1)


class RecentReviewsManager(models.Manager):
    def get_queryset(self):
        queryset = super(RecentReviewsManager, self).get_queryset()
        return queryset.filter(approved=True).order_by('-date_created')


class TopScoredReviewsManager(models.Manager):
    def get_queryset(self):
        queryset = super(TopScoredReviewsManager, self).get_queryset()
        return queryset.filter(approved=True).order_by('-score')


class TopVotedReviewsManager(models.Manager):
    def get_queryset(self):
        queryset = super(TopVotedReviewsManager, self).get_queryset()
        return queryset.filter(approved=True).order_by('-delta_votes')
