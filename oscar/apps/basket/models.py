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