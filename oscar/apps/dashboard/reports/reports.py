import datetime

from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from oscar.apps.dashboard.reports.csv_utils import CsvUnicodeWriter
from oscar.core import utils


class ReportGenerator(object):
    """
    Top-level class that needs to be subclassed to provide a
    report generator.
    """
    filename_template = 'report-%s-to-%s.csv'
    content_type = 'text/csv'
    code = ''
    description = '<insert report description>'
    date_range_field_name = None

    def __init__(self, **kwargs):
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')

        formatter_name = '%s_formatter' % kwargs['formatter']
        self.formatter = self.formatters[formatter_name]()

    def report_description(self):
        return _('%(report_filter)s between %(start_date)s and %(end_date)s') \
            % {'report_filter': self.description,
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

    def filter_with_date_range(self, queryset):
        """
        Filter results based that are within a (possibly open ended) daterange
        """
        # Nothing to do if we don't have a date field
        if not self.date_range_field_name:
            return queryset

        # After the start date
        if self.start_date:
            filter_kwargs = {
                "%s__gt" % self.date_range_field_name: self.start_date,
            }
            queryset = queryset.filter(**filter_kwargs)

        # Before the end of the end date
        if self.end_date:
            end_of_end_date = datetime.datetime.combine(
                self.end_date,
                datetime.time(hour=23, minute=59, second=59)
            )
            filter_kwargs = {
                "%s__lt" % self.date_range_field_name: end_of_end_date,
            }
            queryset = queryset.filter(**filter_kwargs)

        return queryset


class ReportFormatter(object):
    def format_datetime(self, dt):
        if not dt:
            return ''
        return utils.format_datetime(dt, 'DATETIME_FORMAT')

    def format_date(self, d):
        if not d:
            return ''
        return utils.format_datetime(d, 'DATE_FORMAT')

    def filename(self):
        return self.filename_template


class ReportCSVFormatter(ReportFormatter):

    def get_csv_writer(self, file_handle, **kwargs):
        return CsvUnicodeWriter(file_handle, **kwargs)

    def generate_response(self, objects, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' \
            % self.filename(**kwargs)
        self.generate_csv(response, objects)
        return response


class ReportHTMLFormatter(ReportFormatter):

    def generate_response(self, objects, **kwargs):
        return objects
