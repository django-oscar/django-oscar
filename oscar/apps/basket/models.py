from django.conf import settings

from oscar.apps.basket.abstract_models import (
    AbstractBasket, AbstractLine, AbstractLineAttribute)


class InvalidBasketLineError(Exception):
    pass


if 'basket.Basket' not in settings.OSCAR_OVERRIDE_MODELS:
    class Basket(AbstractBasket):
        pass


if 'basket.Line' not in settings.OSCAR_OVERRIDE_MODELS:
    class Line(AbstractLine):
        pass


if 'basket.LineAttribute' not in settings.OSCAR_OVERRIDE_MODELS:
    class LineAttribute(AbstractLineAttribute):
        pass
