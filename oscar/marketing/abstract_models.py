from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

try:
    BANNER_FOLDER = settings.OSCAR_BANNER_FOLDER
except AttributeError: 
    BANNER_FOLDER = 'images/banners/'


class AbstractBanner(models.Model):
    u"""
    A banner image linked to a particular page.
    """
    name = models.CharField(_("Name"), max_length=128)
    page_url = models.CharField(_('URL'), max_length=128, db_index=True)
    link_url = models.URLField(blank=True, null=True, help_text="""This is 
        where the banner links to""")
    image = models.ImageField(upload_to=BANNER_FOLDER)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.page_url)   
        
    def save(self, *args, **kwargs):
        super(AbstractBanner, self).save(*args, **kwargs)
        
    @property    
    def has_link(self):
        return self.link_url != None    

        
    