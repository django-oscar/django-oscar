from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

try:
    BANNER_FOLDER = settings.OSCAR_BANNER_FOLDER
except AttributeError: 
    BANNER_FOLDER = 'images/banners/'
    
try:
    POD_FOLDER = settings.OSCAR_POD_FOLDER
except AttributeError: 
    POD_FOLDER = 'images/pods/'

LEFT, RIGHT = ('Left', 'Right')


class AbstractBanner(models.Model):
    u"""
    A banner image linked to a particular page.
    """
    name = models.CharField(_("Name"), max_length=128)
    page_url = models.CharField(_('URL'), max_length=128, db_index=True)
    display_order = models.PositiveIntegerField(default=0)
    link_url = models.URLField(blank=True, null=True, help_text="""This is 
        where the banner links to""")
    image = models.ImageField(upload_to=BANNER_FOLDER)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        ordering = ['page_url', 'display_order']
        get_latest_by = "date_created"
        
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.page_url)   
        
    def save(self, *args, **kwargs):
        super(AbstractBanner, self).save(*args, **kwargs)
        
    @property    
    def has_link(self):
        return self.link_url != None    
    
    
class AbstractPod(models.Model):
    u"""
    A pod image linked to a particular page.
    """
    POSITION_CHOICES = (
        (LEFT, _("Left of page")),
        (RIGHT, _("Right of page")),
    )
    
    name = models.CharField(_("Name"), max_length=128)
    page_url = models.CharField(_('URL'), max_length=128, db_index=True)
    page_position = models.CharField(_("Position"), max_length=128, choices=POSITION_CHOICES)
    display_order = models.PositiveIntegerField(default=0)
    link_url = models.URLField(blank=True, null=True, help_text="""This is 
        where the pod links to""")
    image = models.ImageField(upload_to=POD_FOLDER)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        ordering = ["page_url", "page_position", 'display_order']
        get_latest_by = "date_created"
        
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.page_url)   
        
    def save(self, *args, **kwargs):
        super(AbstractPod, self).save(*args, **kwargs)
        
    @property    
    def has_link(self):
        return self.link_url != None 

        
    