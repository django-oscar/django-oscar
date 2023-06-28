from oscar.apps.checkout.views import ThankYouView as OscarThankYouView
from oscar.views.decorators import disable_basket


@disable_basket
class ThankYouView(OscarThankYouView):
    pass
