from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class AbstractSynonym(models.Model):
    synonyms = models.CharField(max_length=255,
                                help_text='Comma-separated list of synonyms, optionally mapped using '
                                          '"=>" to what they should be rewritten to.')

    def __str__(self):
        return self.synonyms

    class Meta:
        abstract = True
        app_label = 'search'
        verbose_name = _('Synonym')
        verbose_name_plural = _('Synonyms')
