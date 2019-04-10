import queue
import threading

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import Signer
from django.test import RequestFactory as BaseRequestFactory

from oscar.core.loading import get_class, get_model


class RequestFactory(BaseRequestFactory):
    Basket = get_model('basket', 'basket')
    selector = get_class('partner.strategy', 'Selector')()

    def request(self, user=None, basket=None, **request):
        request = super().request(**request)
        request.user = user or AnonymousUser()
        request.session = SessionStore()
        request._messages = FallbackStorage(request)

        # Mimic basket middleware
        request.strategy = self.selector.strategy(
            request=request, user=request.user)
        request.basket = basket or self.Basket()
        request.basket.strategy = request.strategy
        request.basket_hash = Signer().sign(basket.pk) if basket else None
        request.cookies_to_delete = []

        return request


def run_concurrently(fn, kwargs=None, num_threads=5):
    exceptions = queue.Queue()

    def worker(**kwargs):
        try:
            fn(**kwargs)
        except Exception as exc:
            exceptions.put(exc)
        else:
            exceptions.put(None)
        finally:
            connection.close()

    kwargs = kwargs if kwargs is not None else {}

    # Run them
    threads = [
        threading.Thread(target=worker, name='thread-%d' % i, kwargs=kwargs)
        for i in range(num_threads)
    ]
    try:
        for thread in threads:
            thread.start()
    finally:
        for thread in threads:
            thread.join()

    # Retrieve exceptions
    exceptions = [exceptions.get(block=False) for i in range(num_threads)]
    return [exc for exc in exceptions if exc is not None]
