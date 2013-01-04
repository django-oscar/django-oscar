from django.http import HttpResponse
from django.views import generic

from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class

from oscar.core.reports.views import ReportView

from oscar.apps.catalogue.reports import ProductReportHTMLGenerator
from oscar.apps.catalogue.reports import ProductReportCSVGenerator


report_generator_dict = {
    'product-report-html': ProductReportHTMLGenerator,
    'product-report-csv': ProductReportCSVGenerator,
}

class ReportGeneratorView(ReportView):
    template_name = 'dashboard/reports/generator.html'

    def get_generator_class(self):
        return report_generator_dict[self.kwargs['report_slug']]


class ReportIndexView(generic.base.TemplateView):
    template_name = 'dashboard/reports/index.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(ReportIndexView, self).get_context_data(*args, **kwargs)
        ctx['report_generator_dict'] = report_generator_dict
        return ctx


