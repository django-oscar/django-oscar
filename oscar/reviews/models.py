from django.db import models

from oscar.reviews.abstract_models import AbstractProductReview, AbstractVote


class ProductReview(AbstractProductReview):
    pass

class Vote(AbstractVote):
    pass

