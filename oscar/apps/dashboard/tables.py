from django_tables2 import Table


class DashboardTable(Table):
    class Meta:
        template = 'dashboard/table.html'
        attrs = {'class': 'table table-striped table-bordered'}
