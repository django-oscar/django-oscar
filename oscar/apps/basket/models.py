from exceptions import Exception

from django.core.signals import request_finished
from django.dispatch import receiver

from oscar.apps.basket.abstract_models import (AbstractBasket, AbstractLine, AbstractLineAttribute,
                                          OPEN, MERGED, SAVED, SUBMITTED)


class InvalidBasketLineError(Exception):
    pass


class Basket(AbstractBasket):
    pass

    
class Line(AbstractLine):
    pass


class LineAttribute(AbstractLineAttribute):
    pass