from exceptions import Exception

from django.core.signals import request_finished
from django.dispatch import receiver

from oscar.basket.abstract_models import AbstractBasket, AbstractLine, AbstractLineAttribute


class InvalidBasketLineError(Exception):
    pass


class Basket(AbstractBasket):
    pass

    
class Line(AbstractLine):
    pass


class LineAttribute(AbstractLineAttribute):
    pass