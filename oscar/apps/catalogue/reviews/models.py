from oscar.core.loading import model_registered
from oscar.apps.catalogue.reviews.abstract_models import \
    AbstractProductReview, AbstractVote


if not model_registered('reviews', 'ProductReview'):
    class ProductReview(AbstractProductReview):
        pass


if not model_registered('reviews', 'Vote'):
    class Vote(AbstractVote):
        pass
