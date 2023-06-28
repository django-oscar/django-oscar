from oscar.views.decorators import disable_basket, enable_basket
from tests._site.apps.customer.views import AccountSummaryView


def test_enable_basket_decorator_for_function():
    view = AccountSummaryView.as_view()
    assert not hasattr(view, 'is_basket_enabled')

    decorated_view = enable_basket(view)
    assert decorated_view.is_basket_enabled


def test_disable_basket_decorator_for_function():
    view = AccountSummaryView.as_view()
    assert not hasattr(view, 'is_basket_enabled')

    decorated_view = disable_basket(view)
    assert not decorated_view.is_basket_enabled


def test_enable_basket_decorator_for_class():
    assert not hasattr(AccountSummaryView, 'is_basket_enabled')

    @enable_basket
    class DecoratedAccountSummaryView(AccountSummaryView):
        pass

    assert DecoratedAccountSummaryView.is_basket_enabled


def test_disable_basket_decorator_for_class():
    assert not hasattr(AccountSummaryView, 'is_basket_enabled')

    @disable_basket
    class DecoratedAccountSummaryView(AccountSummaryView):
        pass

    assert not DecoratedAccountSummaryView.is_basket_enabled
