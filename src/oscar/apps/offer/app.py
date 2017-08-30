from oscar.core.application import Application
from oscar.core.loading import get_class


class OfferApplication(Application):
    name = 'offer'


application = OfferApplication()
