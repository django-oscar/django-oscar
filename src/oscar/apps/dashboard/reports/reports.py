from datetime import time

from django.http import HttpResponse
from django.template.defaultfilters import date
from django.utils.translation import gettext_lazy as _

from oscar.core import utils
from oscar.core.compat import UnicodeCSVWriter


class ReportGenerator(object):
    """
    Top-level class that needs to be subclassed to provide a
    report generator.
    """

    filename_template = "report-%s-to-%s.csv"
    content_type = "text/csv"
    code = ""
    description = "<insert report description>"
    date_range_field_name = None
    model_class = None
    queryset = None

    def __init__(self, **kwargs):
        self.start_date = kwargs.get("start_date")
        self.end_date = kwargs.get("end_date")

        formatter_name = "%s_formatter" % kwargs.get("formatter", "HTML")
        # pylint: disable=no-member
        self.formatter = self.formatters[formatter_name]()
        self.queryset = self.get_queryset()
        self.queryset = self.filter_with_date_range(self.queryset)

    def report_description(self):
        return _("%(report_filter)s between %(start_date)s and %(end_date)s") % {
            "report_filter": self.description,
            "start_date": date(self.start_date, "DATE_FORMAT"),
            "end_date": date(self.end_date, "DATE_FORMAT"),
        }

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset

        if not self.model_class:
            raise ValueError(
                "Please define a model_class property on your report generator class, "
                "or override the qet_queryset() method."
            )
        return self.model_class._default_manager.all()

    def generate(self):
        return self.formatter.generate_response(self.queryset)

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
            start_datetime = utils.datetime_combine(self.start_date, time.min)
            filter_kwargs = {
                "%s__gte" % self.date_range_field_name: start_datetime,
            }
            queryset = queryset.filter(**filter_kwargs)

        # Before the end of the end date
        if self.end_date:
            end_datetime = utils.datetime_combine(self.end_date, time.max)
            filter_kwargs = {
                "%s__lte" % self.date_range_field_name: end_datetime,
            }
            queryset = queryset.filter(**filter_kwargs)

        return queryset


class ReportFormatter(object):
    def format_datetime(self, dt):
        if not dt:
            return ""
        return utils.format_datetime(dt, "DATETIME_FORMAT")

    def format_date(self, d):
        if not d:
            return ""
        return utils.format_datetime(d, "DATE_FORMAT")

    def format_timedelta(self, td):
        return utils.format_timedelta(td)

    def filename(self):
        # pylint: disable=no-member
        return self.filename_template


class ReportCSVFormatter(ReportFormatter):
    def get_csv_writer(self, file_handle, **kwargs):
        return UnicodeCSVWriter(open_file=file_handle, **kwargs)

    def generate_response(self, objects, **kwargs):
        response = HttpResponse(content_type="text/csv")
        # pylint: disable=no-member
        response["Content-Disposition"] = "attachment; filename=%s" % self.filename(
            **kwargs
        )
        self.generate_csv(response, objects)
        return response


class ReportHTMLFormatter(ReportFormatter):
    def generate_response(self, objects, **kwargs):
        return objects
