======================
How to handle US taxes
======================

When trading in the US, taxes aren't known until the customer's shipping
address has been entered.  This scenario requires two changes from core Oscar.

Ensure your site strategy returns prices without taxes applied
--------------------------------------------------------------

First, the site strategy should return all prices without tax when the customer
is based in the US.  Oscar provides a :class:`~oscar.apps.partner.strategy.US`
strategy class that uses the :class:`~oscar.apps.partner.strategy.DeferredTax`
mixin to indicate that prices don't include taxes.

See :doc:`the documentation on strategies </topics/prices_and_availability>`
for further guidance on how to replace strategies.

Adjust checkout views to apply taxes once they are known
--------------------------------------------------------

Second, the :class:`~oscar.apps.checkout.session.CheckoutSessionMixin`
should be overridden within your project to apply taxes
to the submission.

.. code-block:: python

    from oscar.apps.checkout import session

    from . import tax

    class CheckoutSessionMixin(session.CheckoutSessionMixin):

        def build_submission(self, **kwargs):
            submission = super().build_submission(
                **kwargs)

            if submission['shipping_address'] and submission['shipping_method']:
                tax.apply_to(submission)

                # Recalculate order total to ensure we have a tax-inclusive total
                submission['order_total'] = self.get_order_totals(
                    submission['basket'],
                    submission['shipping_charge'])

            return submission

An example implementation of the ``tax.py`` module is:

   .. code-block:: python

    from decimal import Decimal as D

    def apply_to(submission):
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
            line.purchase_info.price.tax = unit_tax

        # Note, we change the submission in place - we don't need to
        # return anything from this function
        shipping_charge = submission['shipping_charge']
        if shipping_charge is not None:
            shipping_charge.tax = calculate_tax(
                shipping_charge.excl_tax, rate)

    def calculate_tax(price, rate):
        tax = price * rate
        return tax.quantize(D('0.01'))
