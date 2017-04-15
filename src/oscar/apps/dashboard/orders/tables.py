from django_tables2 import Column, TemplateColumn
from oscar.core.loading import get_class, get_model
from django.utils.translation import ugettext_lazy as _
from oscar.apps.dashboard.tables import TruncatedColumn

DashboardTable = get_class('dashboard.tables', 'DashboardTable')
Order = get_model('order', 'Order')

class OrderTable(DashboardTable):
    select = TemplateColumn(
        verbose_name=' ',
        orderable=False,
        template_code="""
        <input type="checkbox" name="selected_order" class="selected_order" value="32">
    """)
    number = Column(verbose_name=_('Order #'))
    shipping_address = TruncatedColumn(length=100)
    date_placed = Column(verbose_name=_('Purchased on'))
    num_items = Column(verbose_name=_('Items'), attrs={
        'th': {'class': 'text-right'},
        'td': {'class': 'text-right'}
    })
    total_incl_tax = Column(verbose_name=_('Total'), attrs={
        'th': {'class': 'text-right'},
        'td': {'class': 'text-right'}
    })


    class Meta(DashboardTable.Meta):
        model = Order
        fields = [
            'select', 'number', 'date_placed', 'shipping_address',
            'status', 'num_items', 'total_incl_tax'
        ]

