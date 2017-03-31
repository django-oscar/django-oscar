import threading

from django.db import connection

from six.moves import queue


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
