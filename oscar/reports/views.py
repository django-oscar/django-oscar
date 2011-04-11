import csv

from django.http import HttpResponse
from django.shortcuts import render

from oscar.services import import_module
report_forms = import_module('reports.forms', ['ReportForm'])
order_models = import_module('order.models', ['Order'])

class ReportGenerator(object):
    u"""
    Top-level class that needs to be subclassed to provide a 
    report generator.
    """
    
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
    
    def generate(self, response):
        pass
        
class OrderReportGenerator(ReportGenerator):
    
    def generate(self, response):
        #orders = order_models.Order._default_manager.filter(date_placed__gte=self.start_date, date_placed__lt=self.end_date)
        orders = order_models.Order._default_manager.all()
        
        writer = csv.writer(response)
        header_row = ['Order number',
                      'User',
                      'Total incl. tax',
                      'Date placed',]
        writer.writerow(header_row)
        for order in orders:
            row = [order.number, order.user, order.total_incl_tax, order.date_placed]
            writer.writerow(row)


def dashboard(request):
    if 'report_type' in request.GET:
        form = report_forms.ReportForm(request.GET)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename=somefilename.csv'
            
            generator = OrderReportGenerator(start_date, end_date)
            generator.generate(response)
            return response
    else:
        form = report_forms.ReportForm()
    return render(request, 'reports/dashboard.html', locals())