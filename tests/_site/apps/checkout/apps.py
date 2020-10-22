from oscar.apps.checkout import apps


class CheckoutConfig(apps.CheckoutConfig):
    name = 'tests._site.apps.checkout'

    views_with_disabled_basket = ['thank-you']
