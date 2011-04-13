from oscar.services import import_module
order_reports = import_module('order.reports', ['OrderReportGenerator'])
analytics_reports = import_module('analytics.reports', ['ProductReportGenerator', 'UserReportGenerator'])
basket_reports = import_module('basket.reports', ['OpenBasketReportGenerator', 'SubmittedBasketReportGenerator'])     

# @todo Need to make this dynamic by inspecting the apps for reports.py files
generators = [order_reports.OrderReportGenerator,
              analytics_reports.ProductReportGenerator,
              analytics_reports.UserReportGenerator,
              basket_reports.OpenBasketReportGenerator,
              basket_reports.SubmittedBasketReportGenerator,]

def get_report_generators():
    return generators
    
def get_generator(code):
    for generator in generators:
        if generator.code == code:
            return generator
    return None
    
    
