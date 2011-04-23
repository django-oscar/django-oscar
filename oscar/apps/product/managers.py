from django.db import models


class BrowsableItemManager(models.Manager):
    def get_query_set(self):
        return super(BrowsableItemManager, self).get_query_set().filter(parent=None)