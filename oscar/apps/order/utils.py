from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping.methods import Free
from oscar.core.loading import get_class
ShippingAddress = get_model('order', 'ShippingAddress')
Order = get_model('order', 'Order')
Line = get_model('order', 'Line')
LinePrice = get_model('order', 'LinePrice')
LineAttribute = get_model('order', 'LineAttribute')
OrderDiscount = get_model('order', 'OrderDiscount')
order_placed = get_class('order.signals', 'order_placed')


class OrderNumberGenerator(object):
    """
    Simple object for generating order numbers.

    We need this as the order number is often required for payment
    which takes place before the order model has been created.
    """

    def order_number(self, basket):
        """
        Return an order number for a given basket
        """
        return 100000 + basket.id


class OrderCreator(object):
    """
    Places the order by writing out the various models
    """

    def place_order(self, basket, total_incl_tax=None, total_excl_tax=None,
                    user=None, shipping_method=None, shipping_address=None,
                    billing_address=None, order_number=None, status=None, **kwargs):
        """
        Placing an order involves creating all the relevant models based on the
        basket and session data.
        """
        # Only a basket instance is required to place an order - everything else can be set
        # to defaults
        if basket.is_empty:
            raise ValueError(_("Empty baskets cannot be submitted"))
        if not shipping_method:
            shipping_method = Free()
        if total_incl_tax is None or total_excl_tax is None:
            total_incl_tax = basket.total_incl_tax + shipping_method.basket_charge_incl_tax()
            total_excl_tax = basket.total_excl_tax + shipping_method.basket_charge_excl_tax()
        if not order_number:
            generator = OrderNumberGenerator()
            order_number = generator.order_number(basket)
        if not status and hasattr(settings, 'OSCAR_INITIAL_ORDER_STATUS'):
            status = getattr(settings, 'OSCAR_INITIAL_ORDER_STATUS')
        try:
            Order._default_manager.get(number=order_number)
        except Order.DoesNotExist:
            pass
        else:
            raise ValueError(_("There is already an order with number %s") % order_number)

        # Ok - everything seems to be in order, let's place the order
        order = self.create_order_model(user, basket, shipping_address,
                                        shipping_method, billing_address, total_incl_tax,
                                        total_excl_tax, order_number, status, **kwargs)
        for line in basket.all_lines():
            self.create_line_models(order, line)
            self.update_stock_records(line)

        for discount in basket.get_discounts():
            self.create_discount_model(order, discount)
            self.record_discount(discount)

        for voucher in basket.vouchers.all():
            self.record_voucher_usage(order, voucher, user)

        # Send signal for analytics to pick up
        order_placed.send(sender=self, order=order, user=user)

        return order

    def create_order_model(self, user, basket, shipping_address, shipping_method,
                           billing_address, total_incl_tax, total_excl_tax,
                           order_number, status, **extra_order_fields):
        """
        Creates an order model.
        """
        order_data = {'basket_id': basket.id,
                      'number': order_number,
                      'site': Site._default_manager.get_current(),
                      'total_incl_tax': total_incl_tax,
                      'total_excl_tax': total_excl_tax,
                      'shipping_incl_tax': shipping_method.basket_charge_incl_tax(),
                      'shipping_excl_tax': shipping_method.basket_charge_excl_tax(),
                      'shipping_method': shipping_method.name}
        if shipping_address:
            order_data['shipping_address'] = shipping_address
        if billing_address:
            order_data['billing_address'] = billing_address
        if user and user.is_authenticated():
            order_data['user_id'] = user.id
        if status:
            order_data['status'] = status
        if extra_order_fields:
            order_data.update(extra_order_fields)
        order = Order(**order_data)
        order.save()
        return order

    def get_partner_for_product(self, product):
        """
        Return the partner for a product
        """
        if product.has_stockrecord:
            return product.stockrecord.partner
        raise AttributeError(_("No partner found for product '%s'") % product)

    def create_line_models(self, order, basket_line, extra_line_fields=None):
        """
        Create the batch line model.

        You can set extra fields by passing a dictionary as the extra_line_fields value
        """
        partner = self.get_partner_for_product(basket_line.product)
        stockrecord = basket_line.product.stockrecord
        line_data = {'order': order,
                     # Partner details
                     'partner': partner,
                     'partner_name': partner.name,
                     'partner_sku': stockrecord.partner_sku,
                     # Product details
                     'product': basket_line.product,
                     'title': basket_line.product.get_title(),
                     'upc': basket_line.product.upc,
                     'quantity': basket_line.quantity,
                     # Price details
                     'line_price_excl_tax': basket_line.line_price_excl_tax_and_discounts,
                     'line_price_incl_tax': basket_line.line_price_incl_tax_and_discounts,
                     'line_price_before_discounts_excl_tax': basket_line.line_price_excl_tax,
                     'line_price_before_discounts_incl_tax': basket_line.line_price_incl_tax,
                     # Reporting details
                     'unit_cost_price': stockrecord.cost_price,
                     'unit_price_incl_tax': basket_line.unit_price_incl_tax,
                     'unit_price_excl_tax': basket_line.unit_price_excl_tax,
                     'unit_retail_price': stockrecord.price_retail,
                     # Shipping details
                     'est_dispatch_date':  basket_line.product.stockrecord.dispatch_date
                     }
        extra_line_fields = extra_line_fields or {}
        if hasattr(settings, 'OSCAR_INITIAL_LINE_STATUS'):
            if not (extra_line_fields and 'status' in extra_line_fields):
                extra_line_fields['status'] = getattr(settings, 'OSCAR_INITIAL_LINE_STATUS')
        if extra_line_fields:
            line_data.update(extra_line_fields)

        order_line = Line._default_manager.create(**line_data)
        self.create_line_price_models(order, order_line, basket_line)
        self.create_line_attributes(order, order_line, basket_line)
        self.create_additional_line_models(order, order_line, basket_line)

        return order_line

    def update_stock_records(self, line):
        line.product.stockrecord.allocate(line.quantity)

    def create_additional_line_models(self, order, order_line, basket_line):
        """
        Empty method designed to be overridden.

        Some applications require additional information about lines, this
        method provides a clean place to create additional models that
        relate to a given line.
        """
        pass

    def create_line_price_models(self, order, order_line, basket_line):
        """
        Creates the batch line price models
        """
        breakdown = basket_line.get_price_breakdown()
        for price_incl_tax, price_excl_tax, quantity in breakdown:
            LinePrice._default_manager.create(order=order,
                                              line=order_line,
                                              quantity=quantity,
                                              price_incl_tax=price_incl_tax,
                                              price_excl_tax=price_excl_tax)

    def create_line_attributes(self, order, order_line, basket_line):
        """
        Creates the batch line attributes.
        """
        for attr in basket_line.attributes.all():
            LineAttribute._default_manager.create(line=order_line,
                                                  option=attr.option,
                                                  type=attr.option.code,
                                                  value=attr.value)

    def create_discount_model(self, order, discount):
        """
        Creates an order discount model for each discount attached to the basket.
        """
        order_discount = OrderDiscount(order=order,
                                       offer_id=discount['offer'].id,
                                       amount=discount['discount'])
        voucher = discount.get('voucher', None)
        if voucher:
            order_discount.voucher_id = voucher.id
            order_discount.voucher_code = voucher.code
        order_discount.save()

    def record_discount(self, discount):
        discount['offer'].record_usage(discount['discount'])
        if 'voucher' in discount and discount['voucher']:
            discount['voucher'].record_discount(discount['discount'])

    def record_voucher_usage(self, order, voucher, user):
        """
        Updates the models that care about this voucher.
        """
        voucher.record_usage(order, user)
