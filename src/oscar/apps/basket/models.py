from oscar.apps.basket.abstract_models import (
    AbstractBasket, AbstractLine, AbstractLineAttribute)
from oscar.core.loading import is_model_registered

__all__ = [
    'InvalidBasketLineError',
]


class InvalidBasketLineError(Exception):
    pass


if not is_model_registered('basket', 'Basket'):
    class Basket(AbstractBasket):
        pass

    __all__.append('Basket')


if not is_model_registered('basket', 'Line'):
    class Line(AbstractLine):
        pass

    __all__.append('Line')


if not is_model_registered('basket', 'LineAttribute'):
    class LineAttribute(AbstractLineAttribute):
        pass

    __all__.append('LineAttribute')
