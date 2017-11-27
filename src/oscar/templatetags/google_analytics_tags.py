from django import template
from django.templatetags.l10n import unlocalize


register = template.Library()


@register.filter()
def make_gtag_item_list(order):
    items = []
    for line in order.lines.all():
        category = line.category if hasattr(line, 'category') else 'Uncategorised'
        item = {
            'id': order.number,
            'name': line.title,
            'sku': line.partner_sku,
            'category': category,
            'price': unlocalize(line.unit_price_incl_tax),
            'quantity': line.quantity
        }
        items.append(item)
    return items
