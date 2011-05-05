from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render

from oscar.core.loading import import_module
report_forms = import_module('reports.forms', ['ReportForm'])
report_utils = import_module('reports.utils', ['GeneratorRepository'])

def dashboard(request):
    if 'report_type' in request.GET:
        form = report_forms.ReportForm(request.GET)
        if form.is_valid():
            generator = _get_generator(form)
            if not generator.is_available_to(request.user):
                return HttpResponseForbidden("You do not have access to this report")
            
            response = HttpResponse(mimetype=generator.mimetype)
            response['Content-Disposition'] = 'attachment; filename=%s' % generator.filename()
            generator.generate(response)
            return response
    else:
        form = report_forms.ReportForm()
    return render(request, 'oscar/reports/dashboard.html', locals())


def _get_generator(form):
    code = form.cleaned_data['report_type']

    repo = report_utils.GeneratorRepository()
    generator_cls = repo.get_generator(code)
    if not generator_cls:
        raise Http404
    return generator_cls(start_date=form.cleaned_data['start_date'], 
                         end_date=form.cleaned_data['end_date'])
