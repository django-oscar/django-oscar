from django.db import models

from oscar.basket.abstract_models import OPEN, SAVED


class OpenBasketManager(models.Manager):
    """
    For searching/creating OPEN baskets only.
    """
    def get_query_set(self):
        return super(OpenBasketManager, self).get_query_set().filter(status=OPEN)
    
    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(status=OPEN, **kwargs)

    
class SavedBasketManager(models.Manager):
    """
    For searching/creating SAVED baskets only.
    """
    
    def get_query_set(self):
        return super(SavedBasketManager, self).get_query_set().filter(status=SAVED)
    
    def create(self, **kwargs):
        return self.get_query_set().create(status=SAVED, **kwargs)
    
    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(status=SAVED, **kwargs)