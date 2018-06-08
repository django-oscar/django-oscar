from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractSynonym(models.Model):
    synonyms = models.CharField(max_length=255,
                                help_text=_('Comma-separated list of synonyms, optionally mapped using '
                                            '"=>" to what they should be rewritten to.'))

    def __str__(self):
        return self.synonyms

    class Meta:
        abstract = True
        app_label = 'es_search'
        verbose_name = _('Synonym')
        verbose_name_plural = _('Synonyms')
