from django.utils.translation import ungettext, ugettext_noop

from django_tables2 import Table


class DashboardTable(Table):
    _caption = None
    caption_singular = ugettext_noop('{count} Row')
    caption_plural = ugettext_noop('{count} Rows')

    @property
    def caption(self):
        if self._caption:
            return self._caption

        return (ungettext(self.caption_singular, self.caption_plural,
                          self.paginator.count)
                .format(count=self.paginator.count))

    @caption.setter
    def caption(self, caption):
        self._caption = caption

    class Meta:
        template = 'dashboard/table.html'
        attrs = {'class': 'table table-striped table-bordered'}
