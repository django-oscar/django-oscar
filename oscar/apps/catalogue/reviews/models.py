from oscar.core.loading import model_registered
from oscar.apps.catalogue.reviews.abstract_models import \
    AbstractProductReview, AbstractVote


if not model_registered('catalogue', 'ProductReview'):
    class ProductReview(AbstractProductReview):
        pass


if not model_registered('catalogue', 'Vote'):
    class Vote(AbstractVote):
        pass
