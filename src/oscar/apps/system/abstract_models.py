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
    
    #: Date formats for dashboard and UI
    shop_date_format = models.CharField(max_length=32, default="yy-mm-dd")
    shop_time_format = models.CharField(max_length=32, default="hh:ii")
    shop_datetime_format = models.CharField(
        max_length=32,
        default="yy-mm-dd hh:ii"
    )
    
    #: Time for date picker
    shop_date_picker_minute_step = models.PositiveSmallIntegerField(default=15)
    
    #: Dashboard editor settings
    dashboard_editor_plugins = models.CharField(
        max_length=255,
        default="link lists", 
        blank=True
    )
    dashboard_editor_menubar = models.CharField(
        max_length=255,
        default="", 
        blank=True
    )
    dashboard_editor_toolbar_layout = models.CharField(
        max_length=255,
        default="styleselect | bold italic blockquote | bullist numlist | link",
        blank=True
    )
    dashboard_editor_context_menu = models.CharField(
        max_length=255,
        default="copy cut paste link",
        blank=True
    )
    
    class Meta:
        abstract = True
        app_label = 'system'
        verbose_name = _("Configuration")
    
    def as_context(self):
        return {
            'shop_name': self.shop_name,
            'shop_tagline': self.shop_tagline,
            'shop_date_format': self.shop_date_format,
            'shop_time_format': self.shop_time_format,
            'shop_datetime_format': self.shop_datetime_format,
            'shop_date_picker_minute_step': self.shop_date_picker_minute_step,
            'dashboard_editor_plugins': self.dashboard_editor_plugins,
            'dashboard_editor_menubar': self.dashboard_editor_menubar,
            'dashboard_editor_toolbar_layout': self.dashboard_editor_toolbar_layout,
            'dashboard_editor_context_menu': self.dashboard_editor_context_menu,
            'homepage_url': self.homepage_url,
            # Fallback to old settings name for backwards compatibility
            'use_less': self.use_less,
            'google_analytics_id': self.google_analytics_id or None
        }

