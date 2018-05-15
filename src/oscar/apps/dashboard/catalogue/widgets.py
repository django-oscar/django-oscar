from django.urls import reverse_lazy

from oscar.forms.widgets import MultipleRemoteSelect, RemoteSelect


class ProductSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy('dashboard:catalogue-product-lookup')

    def __init__(self, *args, **kwargs):
        super(ProductSelect, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'select2 product-select'


class ProductSelectMultiple(MultipleRemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy('dashboard:catalogue-product-lookup')
