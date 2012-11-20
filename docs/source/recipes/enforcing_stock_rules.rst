==========================
How to enforce stock rules
==========================

You can enforce stock validation rules using signals.  You just need to register a listener to 
the ``BasketLine`` ``pre_save`` signal that checks the line is valid. For example::

    @receiver(pre_save, sender=Line)
    def handle_line_save(sender, **kwargs):
        if 'instance' in kwargs:
            quantity = int(kwargs['instance'].quantity)
            if quantity > 4:
                raise InvalidBasketLineError("You are only allowed to purchase a maximum of 4 of these")