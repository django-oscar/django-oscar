from oscar.core.loading import import_module
order_reports = import_module('order.reports', ['OrderReportGenerator'])
analytics_reports = import_module('analytics.reports', ['ProductReportGenerator', 'UserReportGenerator'])
basket_reports = import_module('basket.reports', ['OpenBasketReportGenerator', 'SubmittedBasketReportGenerator'])     
offer_reports = import_module('offer.reports', ['OfferReportGenerator'])
voucher_reports = import_module('voucher.reports', ['VoucherReportGenerator'])  

class GeneratorRepository(object):
    
    generators = [order_reports.OrderReportGenerator,
                  analytics_reports.ProductReportGenerator,
                  analytics_reports.UserReportGenerator,
                  basket_reports.OpenBasketReportGenerator,
                  basket_reports.SubmittedBasketReportGenerator,
                  voucher_reports.VoucherReportGenerator, 
                  offer_reports.OfferReportGenerator]

    def get_report_generators(self):
        return self.generators
    
    def get_generator(self, code):
        for generator in self.generators:
            if generator.code == code:
                return generator
        return None
    
    
