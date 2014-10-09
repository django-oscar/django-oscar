# -*- coding: utf-8 -*-


from django.utils.translation import ugettext_lazy as _


SORT_BY_SCORE = 1
SORT_BY_RECENCY = 2
SORT_REVIEWS_BY_CHOICES = (
    (SORT_BY_SCORE, _('Score')),
    (SORT_BY_RECENCY, _('Recency')),
)

