from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django_tables2 import A, Column, LinkColumn, TemplateColumn

from oscar.core.loading import get_class

DashboardTable = get_class("dashboard.tables", "DashboardTable")


class UserTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/users/user_row_checkbox.html",
        verbose_name=" ",
        orderable=False,
    )
    email = LinkColumn("dashboard:user-detail", args=[A("id")], accessor="email")
    name = Column(accessor="get_full_name", order_by=("last_name", "first_name"))
    active = Column(accessor="is_active")
    staff = Column(accessor="is_staff")
    date_registered = Column(accessor="date_joined")
    num_orders = Column(
        accessor="userrecord__num_orders", default=0, verbose_name=_("Number of Orders")
    )
    actions = TemplateColumn(
        template_name="oscar/dashboard/users/user_row_actions.html", verbose_name=" "
    )

    icon = "fas fa-users"

    class Meta(DashboardTable.Meta):
        template_name = "oscar/dashboard/users/table.html"

    def order_num_orders(self, queryset, is_descending):
        """
        User record is created only once a user places an order, all such records must
        be at the end of listing, when sorting in descending order, and at the start
        when sorting in ascending.
        """
        if is_descending:
            order_by = F("userrecord__num_orders").desc(nulls_last=True)
        else:
            order_by = F("userrecord__num_orders").asc(nulls_first=True)

        return (queryset.order_by(order_by), True)
