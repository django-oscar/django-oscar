# -*- coding: utf-8 -*-


from django.utils.translation import ugettext_lazy as _


SORT_BY_SCORE = 'Score'
SORT_BY_RECENCY = 'Recency'
SORT_REVIEWS_BY_CHOICES = (
    (SORT_BY_SCORE, _('Score')),
    (SORT_BY_RECENCY, _('Recency')),
)

