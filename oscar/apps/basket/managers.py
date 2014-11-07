from django.db import models


class OpenBasketManager(models.Manager):
    """For searching/creating OPEN baskets only."""
    status_filter = "Open"

    def get_queryset(self):
        return super(OpenBasketManager, self).get_queryset().filter(
            status=self.status_filter)

    def get_or_create(self, **kwargs):
        return self.get_queryset().get_or_create(
            status=self.status_filter, **kwargs)


class SavedBasketManager(models.Manager):
    """For searching/creating SAVED baskets only."""
    status_filter = "Saved"

    def get_queryset(self):
        return super(SavedBasketManager, self).get_queryset().filter(
            status=self.status_filter)

    def create(self, **kwargs):
        return self.get_queryset().create(status=self.status_filter, **kwargs)

    def get_or_create(self, **kwargs):
        return self.get_queryset().get_or_create(
            status=self.status_filter, **kwargs)
