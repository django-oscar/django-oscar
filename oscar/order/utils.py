from django.contrib.sites.models import Site

from oscar.services import import_module
order_models = import_module('order.models', ['ShippingAddress', 'Order', 'Batch', 'BatchLine', 
                                              'BatchLinePrice', 'BatchLineAttribute'])

class OrderCreator(object):
    
    def __init__(self, order_total_calculator):
        self.order_total_calculator = order_total_calculator
    
    def place_order(self, user, basket, shipping_address, shipping_method):
        u"""
        Placing an order involves creating all the relevant models based on the
        basket and session data.
        """
        order = self._create_order_model(user, basket, shipping_address, shipping_method)
        for line in basket.lines.all():
            batch = self._get_or_create_batch_for_line(order, line)
            self._create_line_models(order, batch, line)
        basket.set_as_submitted()
        return order
        
    def _create_order_model(self, user, basket, shipping_address, shipping_method):
        u"""Creates an order model."""
        calc = self.order_total_calculator
        order_data = {'basket': basket,
                      'site': Site.objects.get_current(),
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
    
    def _get_or_create_batch_for_line(self, order, line):
        u"""Returns the batch for a given line, creating it if appropriate."""
        partner = self._get_partner_for_product(line.product)
        batch,_ = order_models.Batch.objects.get_or_create(order=order, partner=partner)
        return batch
    
    def _get_partner_for_product(self, product):
        u"""Returns the partner for a product"""
        if product.has_stockrecord:
            return product.stockrecord.partner
        raise AttributeError("No partner found for product '%s'" % product)
    
    def _create_line_models(self, order, batch, basket_line):
        u"""Creates the batch line model."""
        batch_line = order_models.BatchLine.objects.create(order=order,
                                                           batch=batch, 
                                                           product=basket_line.product, 
                                                           quantity=basket_line.quantity, 
                                                           line_price_excl_tax=basket_line.line_price_excl_tax, 
                                                           line_price_incl_tax=basket_line.line_price_incl_tax)
        self._create_line_price_models(order, batch_line, basket_line)
        self._create_line_attributes(order, batch_line, basket_line)
        
    def _create_line_price_models(self, order, batch_line, basket_line):
        u"""Creates the batch line price models"""
        order_models.BatchLinePrice.objects.create(order=order,
                                                   line=batch_line, 
                                                   quantity=batch_line.quantity, 
                                                   price_incl_tax=basket_line.unit_price_incl_tax,
                                                   price_excl_tax=basket_line.unit_price_excl_tax)
    
    def _create_line_attributes(self, order, batch_line, basket_line):
        u"""Creates the batch line attributes."""
        for attr in basket_line.attributes.all():
            order_models.BatchLineAttribute.objects.create(line=batch_line, type=attr.option.code,
                                                           value=attr.value)
