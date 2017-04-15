from django.utils.translation import ungettext_lazy
from django_tables2 import Column, Table

from django.utils.text import Truncator


class TruncatedColumn(Column):
    def __init__(self, *args, **kwargs):
        self.length = kwargs.pop('length')
        super(TruncatedColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        return Truncator(value).chars(self.length)


class DashboardTable(Table):
    caption = ungettext_lazy('%d Row', '%d Rows')

    def get_caption_display(self):
        # Allow overriding the caption with an arbitrary string that we cannot
        # interpolate the number of rows in
        try:
            return self.caption % self.paginator.count
        except TypeError:
            pass
        return self.caption

    class Meta:
        template = 'dashboard/table.html'
        attrs = {'class': 'table table-hover table-responsive'}
