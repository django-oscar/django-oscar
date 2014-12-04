from decimal import Decimal as D


# State tax rates
STATE_TAX_RATES = {
    'NJ': D('0.07')
}
ZERO = D('0.00')


def apply_to(submission):
    """
    Calculate and apply taxes to a submission
    """
    # This is a dummy tax function which only applies taxes for addresses in
    # New Jersey and New York. In reality, you'll probably want to use a tax
    # service like Avalara to look up the taxes for a given submission.
    shipping_address = submission['shipping_address']
    rate = STATE_TAX_RATES.get(
        shipping_address.state, ZERO)
    for line in submission['basket'].all_lines():
        line_tax = calculate_tax(
            line.line_price_excl_tax_incl_discounts, rate)
        # We need to split the line tax down into a unit tax amount.
        unit_tax = (line_tax / line.quantity).quantize(D('0.01'))
        line.purchase_info.price.tax = unit_tax

    shipping_charge = submission['shipping_charge']
    if shipping_charge is not None:
        shipping_charge.tax = calculate_tax(
            shipping_charge.excl_tax, rate)


def calculate_tax(price, rate):
    tax = price * rate
    return tax.quantize(D('0.01'))
