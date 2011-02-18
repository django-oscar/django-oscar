from django.db import models


class OpenBasketManager(models.Manager):
    u"""For searching/creating OPEN baskets only."""
    status_filter = "Open"
    
    def get_query_set(self):
        return super(OpenBasketManager, self).get_query_set().filter(status=self.status_filter)
    
    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(status=self.status_filter, **kwargs)

    
class SavedBasketManager(models.Manager):
    u"""For searching/creating SAVED baskets only."""
    status_filter = "Saved"
    
    def get_query_set(self):
        return super(SavedBasketManager, self).get_query_set().filter(status=self.status_filter)
    
    def create(self, **kwargs):
        return self.get_query_set().create(status=self.status_filter, **kwargs)
    
    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(status=self.status_filter, **kwargs)