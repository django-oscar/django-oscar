from django.http import HttpResponse
from django.views import generic

from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class

from oscar.core.reports.views import ReportView
from oscar.core.reports.autodiscover import _get_report_generator_map


class ReportMapMixin(object):
    report_generator_map = _get_report_generator_map()


class ReportGeneratorView(ReportView, ReportMapMixin):
    template_name = 'dashboard/reports/generator.html'

    def get_generator_class(self):
        return self.report_generator_map[self.kwargs['report_slug']]


class ReportIndexView(generic.base.TemplateView, ReportMapMixin):
    template_name = 'dashboard/reports/index.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(ReportIndexView, self).get_context_data(*args, **kwargs)
        ctx['report_generator_map'] = self.report_generator_map
        return ctx


