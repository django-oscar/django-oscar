from purl import URL

from babel.numbers import format_currency
from django.conf import settings
from django.utils.translation import to_locale, get_language
from oscar.core.loading import get_model


Category = get_model('catalogue', 'Category')


def clear_price_from_url(url):
    url = URL(url)
    if url.has_query_param('price_min'):
        url = url.remove_query_param('price_min')
    if url.has_query_param('price_max'):
        url = url.remove_query_param('price_max')
    return url.as_string()


def price_url(base_url, price_min, price_max):
    url = URL(clear_price_from_url(base_url))
    url = url.append_query_param('price_min', price_min)
    if price_max:
        url = url.append_query_param('price_max', price_max)

    return url.as_string()


def get_formatted_currency(value, currency):
    kwargs = {
        'currency': currency,
        'locale': to_locale(get_language()),
    }
    kwargs.update(settings.OSCAR_CURRENCY_FORMAT.get(currency, {}))
    return format_currency(value, **kwargs)


def price_display_name(price_min, price_max, currency):
    from_str = get_formatted_currency(price_min, currency)
    if price_max:
        to_str = get_formatted_currency(price_max, currency)

    if not price_max:
        return '%s and above' % from_str
    if price_min == 0:
        return 'Up to %s' % to_str

    return '%s - %s' % (from_str, to_str)


def build_price_ranges(price_ranges, currency, request_url):
    n = len(price_ranges)
    output = []
    for i in range(0,n):
        r = price_ranges[i]
        # For the last range, remove upper bound
        if i == n - 1:
            r['end'] = None

        output.append({
            'url': price_url(request_url, r['start'], r['end']),
            'count': r['count'],
            'name': price_display_name(r['start'], r['end'], currency)
        })

    return output


def category_url(base_url, cat, use_cat_url=False):
    if use_cat_url:
        return cat.get_absolute_url()

    url = URL(base_url)
    if url.has_query_param('category'):
        url = url.remove_query_param('category')
    return url.append_query_param('category', cat.pk).as_string()


def build_category_tree(category, agg, request_url, use_cat_url=False):
    buckets = agg['buckets']
    bucket_counts = {}
    for bucket in buckets:
        bucket_counts[bucket['key']] = bucket['doc_count']

    if category:
        category = int(category)
        cat_obj = Category.objects.get(pk=category)
        ancestors = cat_obj.get_ancestors_and_self()
        children = cat_obj.get_children()
    else:
        ancestors = []
        children = Category.objects.filter(depth=1)

    num_levels = settings.OSCAR_SEARCH.get('CATEGORY_TREE_DEPTH', 1)

    def build_data_list(cats, current_level=1):
        data = []
        for cat in cats:
            n_items = bucket_counts.get(cat.pk, None)
            if n_items:
                item = {
                    'object': cat,
                    'name': cat.name,
                    'count': bucket_counts.get(cat.pk, None),
                    'url': category_url(request_url, cat, use_cat_url)
                }

                if current_level < num_levels:
                    item['children'] = build_data_list(cat.get_children(),
                                                        current_level + 1)
                data.append(item)
        return data

    tree_data = {
        'ancestors': [{
            'object': a,
            'name': a.name,
            'url': category_url(request_url, a, use_cat_url),
            'current': a.pk == category
        } for a in ancestors],
        'children': build_data_list(children)
    }

    return tree_data
