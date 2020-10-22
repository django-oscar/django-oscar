from oscar.views.decorators import enable_basket
from tests._site.apps.customer.views import AccountSummaryView


def test_enable_basket_decorator():
    view = AccountSummaryView.as_view()
    assert not hasattr(view, 'is_basket_enabled')

    decorated_view = enable_basket(view)
    assert decorated_view.is_basket_enabled
