from django.db import models


class BrowsableProductManager(models.Manager):
    def get_query_set(self):
        return super(BrowsableProductManager, self).get_query_set().filter(parent=None)