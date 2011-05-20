from django.contrib.sites.models import Site

from oscar.core.loading import import_module
import_module('order.models', ['ShippingAddress', 'Order', 'Line', 
                               'LinePrice', 'LineAttribute', 'OrderDiscount'], locals())
import_module('order.signals', ['order_placed'], locals())


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
    u"""
    Places the order by writing out the various models
    """
    
    def place_order(self, user, basket, shipping_address, shipping_method, 
                      billing_address, total_incl_tax, total_excl_tax, order_number=None):
        u"""
        Placing an order involves creating all the relevant models based on the
        basket and session data.
        """
        if not order_number:
            generator = OrderNumberGenerator()
            order_number = generator.order_number(basket)
        order = self._create_order_model(user, basket, shipping_address, 
                                         shipping_method, billing_address, total_incl_tax, 
                                         total_excl_tax, order_number)
        for line in basket.all_lines():
            self._create_line_models(order, line)
        for discount in basket.discounts:
            self._create_discount_model(order, discount)
        for voucher in basket.vouchers.all():
            self._record_voucher_usage(order, voucher, user)
        
        basket.set_as_submitted()
        
        # Send signal for analytics to pick up
        order_placed.send(sender=self, order=order, user=user)
        
        return order
        
    def _create_order_model(self, user, basket, shipping_address, shipping_method, 
                               billing_address, total_incl_tax, total_excl_tax, order_number):
        u"""Creates an order model."""
        order_data = {'basket': basket,
                      'number': order_number,
                      'site': Site._default_manager.get_current(),
                      'total_incl_tax': total_incl_tax,
                      'total_excl_tax': total_excl_tax,
                      'shipping_address': shipping_address,
                      'shipping_incl_tax': shipping_method.basket_charge_incl_tax(),
                      'shipping_excl_tax': shipping_method.basket_charge_excl_tax(),
                      'shipping_method': shipping_method.name}
        if billing_address:
            order_data['billing_address'] = billing_address
        if user.is_authenticated():
            order_data['user_id'] = user.id
        order = Order(**order_data)
        order.save()
        return order
    
    def _get_partner_for_product(self, product):
        u"""Returns the partner for a product"""
        if product.has_stockrecord:
            return product.stockrecord.partner
        raise AttributeError("No partner found for product '%s'" % product)
    
    def _create_line_models(self, order, basket_line):
        u"""Creates the batch line model."""
        partner = self._get_partner_for_product(basket_line.product)
        stockrecord = basket_line.product.stockrecord
        order_line = Line(order=order,
                          # Partner details
                          partner=partner,
                          partner_name=partner.name,
                          partner_sku=stockrecord.partner_sku,
                          # Product details
                          product=basket_line.product, 
                          title=basket_line.product.get_title(),
                          quantity=basket_line.quantity,
                          # Price details 
                          line_price_excl_tax=basket_line.line_price_excl_tax_and_discounts, 
                          line_price_incl_tax=basket_line.line_price_incl_tax_and_discounts,
                          line_price_before_discounts_excl_tax=basket_line.line_price_excl_tax,
                          line_price_before_discounts_incl_tax=basket_line.line_price_incl_tax,
                          # Reporting details
                          unit_cost_price = stockrecord.cost_price,
                          unit_site_price = stockrecord.price_incl_tax,
                          unit_retail_price = stockrecord.price_retail,
                          # Shipping details
                          est_dispatch_date = basket_line.product.stockrecord.dispatch_date
                          )
        order_line.save()
        self._create_line_price_models(order, order_line, basket_line)
        self._create_line_attributes(order, order_line, basket_line)
        
    def _create_line_price_models(self, order, order_line, basket_line):
        u"""Creates the batch line price models"""
        breakdown = basket_line.get_price_breakdown()
        for price_incl_tax, price_excl_tax, quantity in breakdown:
            LinePrice._default_manager.create(order=order,
                                              line=order_line, 
                                              quantity=quantity, 
                                              price_incl_tax=price_incl_tax,
                                              price_excl_tax=price_excl_tax)
    
    def _create_line_attributes(self, order, order_line, basket_line):
        u"""Creates the batch line attributes."""
        for attr in basket_line.attributes.all():
            LineAttribute._default_manager.create(line=order_line,
                                                   option=attr.option, 
                                                   type=attr.option.code,
                                                   value=attr.value)
            
    def _create_discount_model(self, order, discount):
        u"""
        Creates an order discount model for each discount attached to the basket.
        """
        order_discount = OrderDiscount(order=order, offer=discount['offer'], amount=discount['discount'])
        if discount['voucher']:
            order_discount.voucher = discount['voucher']
            order_discount.voucher_code = discount['voucher'].code
        order_discount.save()
        
    def _record_voucher_usage(self, order, voucher, user):
        u"""
        Updates the models that care about this voucher.
        """
        voucher.record_usage(order, user)
        voucher.num_orders += 1
        voucher.save()
