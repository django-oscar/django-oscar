from django_tables2 import A, Column, LinkColumn, TemplateColumn

from oscar.core.loading import get_class

DashboardTable = get_class('dashboard.tables', 'DashboardTable')


class UserTable(DashboardTable):
    check = TemplateColumn(
        template_name='dashboard/users/user_row_checkbox.html',
        verbose_name=' ', orderable=False)
    email = LinkColumn('dashboard:user-detail', args=[A('id')],
                       accessor='email')
    name = Column(accessor='get_full_name',
                  order_by=('last_name', 'first_name'))
    active = Column(accessor='is_active')
    staff = Column(accessor='is_staff')
    date_registered = Column(accessor='date_joined')
    num_orders = Column(accessor='orders.count', orderable=False)
    actions = TemplateColumn(
        template_name='dashboard/users/user_row_actions.html',
        verbose_name=' ')

    icon = "group"

    class Meta(DashboardTable.Meta):
        template = 'dashboard/users/table.html'
