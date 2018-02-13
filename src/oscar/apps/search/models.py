from django.db import models


class Synonym(models.Model):
    synonyms = models.CharField(max_length=255,
                                help_text='Comma-separated list of synonyms, optionally mapped using '
                                          '"=>" to what they should be rewritten to.')

    def __str__(self):
        return self.synonyms
