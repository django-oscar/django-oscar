from django.views import generic
from django.http import HttpResponse
from django.template import RequestContext

from .generators import Generator


class ReportView(generic.edit.FormView):
    """
    This class is meant to be used when creating a report view
    """

    generator_class = Generator
    template_name = 'dashboard/reports/base.html'

    def get_generator_class(self, *args, **kwargs):
        return self.generator_class

    def get_generator(self, *args, **kwargs):
        return self.get_generator_class()(*args, **kwargs)

    def get_form_class(self):
        return self.generator_class.report_class.form_class

    def get(self, *args, **kwargs):
        self.generator_class = self.get_generator_class()
        return super(ReportView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.generator_class = self.get_generator_class()
        return super(ReportView, self).post(*args, **kwargs)

    def form_valid(self, form):
        context = RequestContext(self.request)
        self.generator = self.get_generator(context, form.cleaned_data)
        self.generator.run()
        return HttpResponse(self.generator.output_text,
                    content_type=self.generator.formatter.content_type)

