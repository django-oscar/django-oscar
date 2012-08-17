from django.template.defaultfilters import date
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _


class ReportGenerator(object):
    """
    Top-level class that needs to be subclassed to provide a
    report generator.
    """
    filename_template = 'report-%s-to-%s.csv'
    mimetype = 'text/csv'
    code = ''
    description = '<insert report description>'

    def __init__(self, **kwargs):
        if 'start_date' in kwargs and 'end_date' in kwargs:
            self.start_date = kwargs['start_date']
            self.end_date = kwargs['end_date']

        self.formatter = self.formatters['%s_formatter' % kwargs['formatter']]()

    def report_description(self):
        return _(u'%(report_filter)s between %(start_date)s and %(end_date)s') % {
            'report_filter': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }


    def generate(self, response):
        pass

    def filename(self):
        """
        Returns the filename for this report
        """
        return self.formatter.filename()

    def is_available_to(self, user):
        """
        Checks whether this report is available to this user
        """
        return user.is_staff


class ReportFormatter(object):
    def format_datetime(self, dt):
        return date(dt, 'DATETIME_FORMAT')

    def format_date(self, d):
        return date(d, 'DATE_FORMAT')

    def filename(self):
        return self.filename_template


class ReportCSVFormatter(ReportFormatter):

    def generate_response(self, objects, **kwargs):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % self.filename(**kwargs)
        self.generate_csv(response, objects)
        return response


class ReportHTMLFormatter(ReportFormatter):

    def generate_response(self, objects, **kwargs):
        return objects
