from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteMixin(models.Model):
    site = models.ForeignKey('sites.Site', verbose_name=_("Site"), null=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True
