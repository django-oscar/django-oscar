from django.db import models


class OpenBasketManager(models.Manager):
    def get_query_set(self):
        return super(OpenBasketManager, self).get_query_set().filter(status="Open")