from django.db import models

class AbstractAddress(models.Model):
    title = models.CharField(max_length=64, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, null=True)
    line3 = models.CharField(max_length=255, blank=True, null=True)
    line4 = models.CharField(max_length=255, blank=True, null=True)
    postcode = models.CharField(max_length=64)
    # @todo: Create a country model to use as a foreign key
    country = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        abstract = True
        
    def get_salutation(self):
        return "%s %s %s" % (self.title, self.first_name, self.last_name)    
        
    def __unicode__(self):
        parts = (self.get_salutation(), self.line1, self.line2, self.line3, self.line4,
                 self.postcode, self.country)
        return ", ".join([part for part in parts if part])
