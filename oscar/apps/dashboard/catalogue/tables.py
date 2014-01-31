from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from django_tables2 import Table, Column, LinkColumn, TemplateColumn, A

Product = get_model('catalogue', 'Product')


class ProductTable(Table):
    title = TemplateColumn(
        template_name='dashboard/catalogue/product_row_title.html',
        order_by='title', accessor=A('get_title'))
    image = TemplateColumn(
        template_name='dashboard/catalogue/product_row_image.html',
        orderable=False)
    product_class = Column(verbose_name=_("Type"),
                           accessor=A('get_product_class.name'),
                           order_by=('product_class__name'))
    parent = LinkColumn('dashboard:catalogue-product',
                        verbose_name=_("Parent"), args=[A('parent.pk')],
                        accessor=A('parent.title'))
    children = Column(accessor=A('children.count'), orderable=False)
    stock_records = Column(accessor=A('stockrecords.count'), orderable=False)
    actions = TemplateColumn(
        template_name='dashboard/catalogue/product_row_actions.html',
        orderable=False)

    class Meta:
        template = 'dashboard/table.html'
        model = Product
        attrs = {'class': 'table table-striped table-bordered'}
        fields = ('upc', 'status')
        sequence = ('title', 'upc', 'image', 'product_class', 'status',
                    'parent', 'children', 'stock_records', '...', 'actions')
