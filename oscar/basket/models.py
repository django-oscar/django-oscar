from exceptions import Exception

from django.db.models.signals import pre_save
from django.core.signals import request_finished
from django.dispatch import receiver

from oscar.basket.abstract_models import *


class InvalidBasketLineError(Exception):
    pass


class Basket(AbstractBasket):
    pass

    
class Line(AbstractLine):
    pass


class LineAttribute(AbstractLineAttribute):
    pass


@receiver(pre_save, sender=Line)
def handle_line_save(sender, **kwargs):
    if 'instance' in kwargs:
        quantity = int(kwargs['instance'].quantity)
        if quantity > 4:
            raise InvalidBasketLineError("You are only allowed to purchase a maximum of 4 of these")