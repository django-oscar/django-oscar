======================
How to handle US taxes
======================

When trading in the US, taxes aren't known until the customer's shipping
address has been entered.  This scenario requires two changes from core Oscar.

First, the site strategy should return all prices without tax when the customer
is based in the US.  See 
:doc:`the documentation on strategies </topics/prices_and_availability>`
for guidance on how to replace strategies.

Second, the 
:class:`~oscar.apps.checkout.views.PaymentDetailsView`
checkout view should be
overridden to calculate taxes on the basket within the 
:func:`~oscar.apps.checkout.views.PaymentDetailsView.build_submission`
method.

.. code-block:: python

    from oscar.apps.checkout import views

    from . import tax

    # Override core Oscar view class
    class PaymentDetailsView(views.PaymentDetailsView):
        
        # Override build_submission to ensure taxes are applied before
        # attempting to place an order
        def build_submission(self, **kwargs):
            submission = super(PaymentDetailsView, self).build_submission(**kwargs)

            # Apply taxes (in place)
            tax.apply_to_submission(submission)

            # Recalculate order total to ensure we have a tax-inclusive total
            submission['order_total'] = self.get_order_totals(
                submission['basket'],
                shipping_method=submission['shipping_method'])

            return submission

An example implementation of the ``tax.py`` module is:

   .. code-block:: python

    from decimal import Decimal as D

    def apply_tax_to_submission(submission):
        # Assume 7% sales tax on sales to New Jersey  You could instead use an
        # external service like Avalara to look up the appropriates taxes.
        STATE_TAX_RATES = {
            'NJ': D('0.07')
        }
        shipping_address = submission['shipping_address']
        rate = STATE_TAX_RATES.get(
            shipping_address.state, D('0.00'))
        for line in submission['basket'].all_lines():
            line_tax = calculate_tax(
                line.line_price_excl_tax_incl_discounts, rate)
            unit_tax = (line_tax / line.quantity).quantize(D('0.01'))
            line.stockinfo.price.tax = unit_tax

        # Note, we change the submission in place - we don't need to
        # return anything from this function
        shipping_method = submission['shipping_method']
        shipping_method.tax = calculate_tax(
            shipping_method.charge_incl_tax, rate)

        def calculate_tax(price, rate):
            tax = price * rate
            return tax.quantize(D('0.01'))
