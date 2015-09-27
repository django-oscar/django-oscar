from oscar.core.loading import get_class, get_classes

OrderReportGenerator = get_class('order.reports', 'OrderReportGenerator')
ProductReportGenerator, UserReportGenerator \
    = get_classes('analytics.reports', ['ProductReportGenerator',
                                        'UserReportGenerator'])
OpenBasketReportGenerator, SubmittedBasketReportGenerator \
    = get_classes('basket.reports', ['OpenBasketReportGenerator',
                                     'SubmittedBasketReportGenerator'])
OfferReportGenerator = get_class('offer.reports', 'OfferReportGenerator')
VoucherReportGenerator = get_class('voucher.reports', 'VoucherReportGenerator')


class GeneratorRepository(object):

    generators = [OrderReportGenerator,
                  ProductReportGenerator,
                  UserReportGenerator,
                  OpenBasketReportGenerator,
                  SubmittedBasketReportGenerator,
                  VoucherReportGenerator,
                  OfferReportGenerator]

    def get_report_generators(self):
        return self.generators

    def get_generator(self, code):
        for generator in self.generators:
            if generator.code == code:
                return generator
        return None
