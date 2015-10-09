from django.core.urlresolvers import reverse_lazy

from oscar.forms.widgets import MultipleRemoteSelect, RemoteSelect


class ProductSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy('dashboard:catalogue-product-lookup')


class ProductSelectMultiple(MultipleRemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy('dashboard:catalogue-product-lookup')
    is_multiple = True
