from contextlib import contextmanager

from mock import Mock


@contextmanager
def mock_signal_receiver(signal, wraps=None, **kwargs):
    """
    Temporarily attaches a receiver to the provided ``signal`` within the scope
    of the context manager.

    Example use::

        with mock_signal_receiver(signal) as receiver:
            # Do the thing that should trigger the signal
            self.assertEqual(receiver.call_count, 1)

    Implementation based on:
    https://github.com/dcramer/mock-django/blob/master/mock_django/signals.py
    """
    if wraps is None:
        def wraps(*args, **kwargs):
            return None

    receiver = Mock(wraps=wraps)
    signal.connect(receiver, **kwargs)
    yield receiver
    signal.disconnect(receiver)
