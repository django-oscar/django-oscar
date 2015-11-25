from django.db import models


class ApprovedReviewsManager(models.Manager):
    def get_queryset(self):
        queryset = super(ApprovedReviewsManager, self).get_queryset()
        return queryset.filter(status=self.model.APPROVED)
