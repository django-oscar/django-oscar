from django.db import models


class OrderSummary(models.Model):
    date_from = models.DateField()
    date_to = models.DateField()

    def __unicode__(self):
        return u"%s - %s : OrderSummary" % (self.date_from, self.date_to)
