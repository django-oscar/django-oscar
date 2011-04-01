from django.contrib.sites.models import Site

from oscar.services import import_module
order_models = import_module('order.models', ['ShippingAddress', 'Order', 'Line', 
                                              'LinePrice', 'LineAttribute'])


class OrderNumberGenerator(object):
    u"""
    Simple object for generating order numbers.

    We need this as the order number is often required for payment
    which takes place before the order model has been created.
    """

    def order_number(self, basket):
        u"""
        Return an order number for a given basket
        """
        return 100000 + basket.id


class OrderCreator(object):
    
    def __init__(self, order_total_calculator):
        self.order_total_calculator = order_total_calculator
    
    def place_order(self, user, basket, shipping_address, shipping_method, order_number=None):
        u"""
        Placing an order involves creating all the relevant models based on the
        basket and session data.
        """
        if not order_number:
            generator = OrderNumberGenerator()
            order_number = generator.order_number(basket)
        order = self._create_order_model(user, basket, shipping_address, shipping_method, order_number)
        for line in basket.lines.all():
            self._create_line_models(order, line)
        basket.set_as_submitted()
        return order
        
    def _create_order_model(self, user, basket, shipping_address, shipping_method, order_number):
        u"""Creates an order model."""
        calc = self.order_total_calculator
        order_data = {'basket': basket,
                      'number': order_number,
                      'site': Site._default_manager.get_current(),
                      'total_incl_tax': calc.order_total_incl_tax(basket, shipping_method),
                      'total_excl_tax': calc.order_total_excl_tax(basket, shipping_method),
                      'shipping_address': shipping_address,
                      'shipping_incl_tax': shipping_method.basket_charge_incl_tax(),
                      'shipping_excl_tax': shipping_method.basket_charge_excl_tax(),
                      'shipping_method': shipping_method.name}
        if user.is_authenticated():
            order_data['user_id'] = user.id
        order = order_models.Order(**order_data)
        order.save()
        return order
    
    def _get_partner_for_product(self, product):
        u"""Returns the partner for a product"""
        if product.has_stockrecord:
            return product.stockrecord.partner
        raise AttributeError("No partner found for product '%s'" % product)
    
    def _create_line_models(self, order, basket_line):
        u"""Creates the batch line model."""
        order_line = order_models.Line(order=order,
                                      partner=self._get_partner_for_product(basket_line.product),
                                      product=basket_line.product, 
                                      title=basket_line.product.get_title(),
                                      quantity=basket_line.quantity, 
                                      line_price_excl_tax=basket_line.line_price_excl_tax, 
                                      line_price_incl_tax=basket_line.line_price_incl_tax)
        if basket_line.product.has_stockrecord:
            order_line.partner_reference = basket_line.product.stockrecord.partner_reference
        order_line.save()
        self._create_line_price_models(order, order_line, basket_line)
        self._create_line_attributes(order, order_line, basket_line)
        
    def _create_line_price_models(self, order, order_line, basket_line):
        u"""Creates the batch line price models"""
        order_models.LinePrice._default_manager.create(order=order,
                                                   line=order_line, 
                                                   quantity=order_line.quantity, 
                                                   price_incl_tax=basket_line.unit_price_incl_tax,
                                                   price_excl_tax=basket_line.unit_price_excl_tax)
    
    def _create_line_attributes(self, order, order_line, basket_line):
        u"""Creates the batch line attributes."""
        for attr in basket_line.attributes.all():
            order_models.LineAttribute._default_manager.create(line=order_line, type=attr.option.code,
                                                      value=attr.value)
