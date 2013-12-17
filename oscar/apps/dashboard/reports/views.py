from django.http import HttpResponseForbidden, Http404
from django.template.response import TemplateResponse
from django.views.generic import ListView
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class
ReportForm = get_class('dashboard.reports.forms', 'ReportForm')
GeneratorRepository = get_class('dashboard.reports.utils',
                                'GeneratorRepository')


class IndexView(ListView):
    template_name = 'dashboard/reports/index.html'
    paginate_by = 25
    context_object_name = 'objects'
    report_form_class = ReportForm
    generator_repository = GeneratorRepository

    def _get_generator(self, form):
        code = form.cleaned_data['report_type']

        repo = self.generator_repository()
        generator_cls = repo.get_generator(code)
        if not generator_cls:
            raise Http404()

        download = form.cleaned_data['download']
        formatter = 'CSV' if download else 'HTML'

        return generator_cls(start_date=form.cleaned_data['date_from'],
                             end_date=form.cleaned_data['date_to'],
                             formatter=formatter)

    def get(self, request, *args, **kwargs):
        if 'report_type' in request.GET:
            form = self.report_form_class(request.GET)
            if form.is_valid():
                generator = self._get_generator(form)
                if not generator.is_available_to(request.user):
                    return HttpResponseForbidden(_("You do not have access to"
                                                   " this report"))

                report = generator.generate()

                if form.cleaned_data['download']:
                    return report
                else:
                    self.set_list_view_attrs(generator, report)
                    context = self.get_context_data(object_list=self.queryset)
                    context['form'] = form
                    context['description'] = generator.report_description()
                    return self.render_to_response(context)
        else:
            form = self.report_form_class()
        return TemplateResponse(request, self.template_name, {'form': form})

    def set_list_view_attrs(self, generator, report):
        self.template_name = generator.filename()
        self.object_list = self.queryset = report
