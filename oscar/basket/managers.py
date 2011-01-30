from django.db import models


class OpenBasketManager(models.Manager):
    
    def get_query_set(self):
        return super(OpenBasketManager, self).get_query_set().filter(status="Open")
    
    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(status="Open", **kwargs)
    
class SavedBasketManager(models.Manager):
    
    def get_query_set(self):
        return super(SavedBasketManager, self).get_query_set().filter(status="Saved")
    
    def create(self, **kwargs):
        return self.get_query_set().create(status="Saved", **kwargs)
    
    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(status="Saved", **kwargs)