from django.db import models


class OrderSummary(models.Model):
    date_from = models.DateField()
    date_to = models.DateField()

    def __unicode__(self):
        return u"%s - %s : OrderSummary" % (self.date_from, self.date_to)


#    date_formats = ('%d/%m/%Y',)
#    date_from = forms.DateField(required=False, label="Date from", input_formats=date_formats)
#    date_to = forms.DateField(required=False, label="Date to", input_formats=date_formats)
