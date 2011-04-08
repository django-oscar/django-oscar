from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

BANNER_FOLDER = getattr(settings, 'OSCAR_BANNER_FOLDER', 'images/promotions/banners')
POD_FOLDER = getattr(settings, 'OSCAR_POD_FOLDER', 'images/promotions/pods')
BANNER, LEFT_POD, RIGHT_POD = ('Banner', 'Left pod', 'Right pod')


class AbstractPromotion(models.Model):
    u"""
    A promotion model.

    This is effectively a link for directing users to different parts of the site.
    It can have two images associated with it.

    """
    name = models.CharField(_("Name"), max_length=128)
    link_url = models.URLField(blank=True, null=True, help_text="""This is 
        where this promotion links to""")

    # Three ways of supplying the content
    banner_image = models.ImageField(upload_to=BANNER_FOLDER, blank=True, null=True)
    pod_image = models.ImageField(upload_to=BANNER_FOLDER, blank=True, null=True)
    raw_html = models.TextField(blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['date_created']
        get_latest_by = "date_created"
        
    def __unicode__(self):
        if not self.link_url:
            return self.name
        return "%s (%s)" % (self.name, self.link_url)   
        
    def save(self, *args, **kwargs):
        # @todo check that at least one of the three content fields is set
        super(AbstractPromotion, self).save(*args, **kwargs)
        
    @property    
    def has_link(self):
        return self.link_url != None    

    def get_banner_html(self):
        return self._get_html('banner_image')

    def get_pod_html(self):
        return self._get_html('pod_image')

    def _get_html(self, image_field):
        if self.raw_html:
            return self.raw_html
        try:
            image = getattr(self, image_field)
            if self.link_url:
                return '<a href="%s"><img src="%s" alt="%s" /></a>' % (self._get_link(), image.url, self.name)
            return '<img src="%s" alt="%s" />' % (image.url, self.name)
        except AttributeError:
            return ''

    def _get_link(self):
        return '/promotions/redirect/1/'


class AbstractPagePromotion(models.Model):
    u"""
    A promotion embedded on a particular page.
    """
    promotion = models.ForeignKey('promotions.Promotion')
    page_url = models.CharField(_('URL'), max_length=128, db_index=True)
    
    POSITION_CHOICES = (
        (BANNER, _("Banner")),
        (LEFT_POD, _("Pod on left-hand side of page")),
        (RIGHT_POD, _("Pod on right-hand side of page")),
    )
    position = models.CharField(_("Position"), max_length=100, help_text="Position on page", choices=POSITION_CHOICES)
    display_order = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-clicks']

    def record_click(self):
        self.clicks += 1
        self.save()


    def __unicode__(self):
        return u"%s on %s" % (self.promotion, self.page_url)
        
    