from decimal import Decimal as D


class OfferApplications(object):
    """
    A collection of offer applications and the discounts that they give.

    Each offer application is stored as a dict which has fields for:

    * The offer that led to the successful application
    * The result instance
    * The number of times the offer was successfully applied
    """
    def __init__(self):
        self.applications = {}

    def __iter__(self):
        return self.applications.values().__iter__()

    def __len__(self):
        return len(self.applications)

    def add(self, offer, result):
        if offer.id not in self.applications:
            self.applications[offer.id] = {
                'offer': offer,
                'result': result,
                'name': offer.name,
                'description': result.description,
                'voucher': offer.get_voucher(),
                'freq': 0,
                'discount': D('0.00')}
        self.applications[offer.id]['discount'] += result.discount
        self.applications[offer.id]['freq'] += 1

    @property
    def offer_discounts(self):
        """
        Return basket discounts from offers (but not voucher offers)
        """
        discounts = []
        for application in self.applications.values():
            if not application['voucher'] and application['discount'] > 0:
                discounts.append(application)
        return discounts

    @property
    def voucher_discounts(self):
        """
        Return basket discounts from vouchers.
        """
        discounts = []
        for application in self.applications.values():
            if application['voucher'] and application['discount'] > 0:
                discounts.append(application)
        return discounts

    @property
    def shipping_discounts(self):
        """
        Return shipping discounts
        """
        discounts = []
        for application in self.applications.values():
            if application['result'].affects_shipping:
                discounts.append(application)
        return discounts

    @property
    def grouped_voucher_discounts(self):
        """
        Return voucher discounts aggregated up to the voucher level.

        This is different to the voucher_discounts property as a voucher can
        have multiple offers associated with it.
        """
        voucher_discounts = {}
        for application in self.voucher_discounts:
            voucher = application['voucher']
            if voucher.code not in voucher_discounts:
                voucher_discounts[voucher.code] = {
                    'voucher': voucher,
                    'discount': application['discount'],
                }
            else:
                voucher_discounts[voucher.code] += application.discount
        return voucher_discounts.values()

    @property
    def post_order_actions(self):
        """
        Return successful offer applications which didn't lead to a discount
        """
        applications = []
        for application in self.applications.values():
            if application['result'].affects_post_order:
                applications.append(application)
        return applications

    @property
    def offers(self):
        """
        Return a dict of offers that were successfully applied
        """
        return dict([(a['offer'].id, a['offer']) for a in
                     self.applications.values()])
