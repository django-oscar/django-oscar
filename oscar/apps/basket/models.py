from oscar.core.loading import model_registered
from oscar.apps.basket.abstract_models import (
    AbstractBasket, AbstractLine, AbstractLineAttribute)


class InvalidBasketLineError(Exception):
    pass


if not model_registered('basket', 'Basket'):
    class Basket(AbstractBasket):
        pass


if not model_registered('basket', 'Line'):
    class Line(AbstractLine):
        pass


if not model_registered('basket', 'LineAttribute'):
    class LineAttribute(AbstractLineAttribute):
        pass
