from itertools import zip_longest

from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model


def generate_code(length, chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789',
                  group_length=4, separator='-'):
    """Create a string of 16 chars grouped by 4 chars."""
    random_string = (i for i in get_random_string(length=length, allowed_chars=chars))
    return separator.join(
        ''.join(filter(None, a))
        for a in zip_longest(*[random_string] * group_length)
    )


def get_unused_code(length=12, group_length=4, separator='-'):
    """Generate a code, check in the db if it already exists and return it.

    i.e. ASDA-QWEE-DFDF-KFGG

    :param int length: the number of characters in the code
    :param int group_length: length of character groups separated by separator kwarg ('-' by default)
    :param str separator: separator string for voucher code
    :return: voucher code
    :rtype: str

    """
    Voucher = get_model('voucher', 'Voucher')
    while True:
        code = generate_code(length, group_length=group_length,
                             separator=separator)
        if not Voucher.objects.filter(code=code).exists():
            return code


def get_offer_name(voucher_name):
    """
    Return the name used for the auto-generated offer created
    when a voucher is created through the dashboard.
    """
    return _("Offer for voucher '%s'") % voucher_name
