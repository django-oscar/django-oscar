import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test.client import RequestFactory as BaseRequestFactory

from oscar.core.loading import get_class, get_model


@pytest.fixture()
def rf():
    """RequestFactory instance"""
    return RequestFactory()


class RequestFactory(BaseRequestFactory):
    Basket = get_model("basket", "basket")
    selector = get_class("partner.strategy", "Selector")()

    def request(self, user=None, **request):
        request = super().request(**request)
        request.user = user or AnonymousUser()
        request.session = SessionStore()
        request._messages = FallbackStorage(request)

        request.basket = self.Basket()
        request.basket_hash = None
        strategy = self.selector.strategy(request=request, user=request.user)
        # pylint: disable=no-member
        request.strategy = request.basket.strategy = strategy

        return request
