from decimal import ROUND_HALF_UP
from decimal import Decimal as D


def tax_subtract(price, tax_percentage=21):
    """Subtract the given `tax_percentage` from the given `price`."""
    if price is None:
        return None

    result = price / ((100 + tax_percentage) / D(100))
    return result.quantize(D("0.01"), ROUND_HALF_UP)


def tax_add(price, tax_percentage=21):
    """Add the given `tax_percentage` to the given `price`."""
    if price is None:
        return None

    result = price * ((100 + tax_percentage) / D(100))
    return result.quantize(D("0.01"), ROUND_HALF_UP)
