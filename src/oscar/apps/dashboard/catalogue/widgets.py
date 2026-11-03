from django.urls import reverse_lazy

from oscar.forms.widgets import MultipleRemoteSelect, RemoteSelect


class ProductSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy("dashboard:catalogue-product-lookup")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "select2 product-select"


class ProductSelectMultiple(MultipleRemoteSelect):
    # Implemented as separate class instead of just calling
    # AjaxSelect(data_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy("dashboard:catalogue-product-lookup")


class PartnerSelect(RemoteSelect):
    # Implemented as separate class instead of just calling
    # RemoteSelect(lookup_url=...) for overridability and backwards compatibility
    lookup_url = reverse_lazy("dashboard:catalogue-partner-lookup")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "select2 partner-select"
