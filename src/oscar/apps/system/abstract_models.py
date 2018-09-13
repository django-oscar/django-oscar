from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractConfiguration(models.Model):
    """ System configuration 
    
    """
    shop_name = models.CharField(max_length=64)
    shop_tagline = models.CharField(max_length=256)
    homepage_url = models.CharField(max_length=256, default='/')
    
    #: Use css by default
    use_less = models.BooleanField(default=False)
    
    #: Analytics ID
    google_analytics_id = models.CharField(max_length=256, blank=True,
                                           null=True)
    
    class Meta:
        abstract = True
        app_label = 'system'
        verbose_name = _("Configuration")
    
    def as_context(self):
        return {
            'shop_name': self.shop_name,
            'shop_tagline': self.shop_tagline,
            'homepage_url': self.homepage_url,
            # Fallback to old settings name for backwards compatibility
            'use_less': self.use_less,
            'google_analytics_id': self.google_analytics_id or None
        }

