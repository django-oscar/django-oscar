import warnings

import cProfile
import pstats
import time

from oscar.utils.deprecation import RemovedInOscar15Warning


def profile(fn):
    """
    Profile the decorated function, storing the profile output in /tmp

    Inspired by
    https://speakerdeck.com/rwarren/a-brief-intro-to-profiling-in-python
    """

    warnings.warn(
        "The profile() decorator will be removed in Oscar 1.5",
        RemovedInOscar15Warning)

    def profiled_fn(*args, **kwargs):
        filepath = "/tmp/%s.profile" % fn.__name__
        prof = cProfile.Profile()

        start = time.time()
        result = prof.runcall(fn, *args, **kwargs)
        duration = time.time() - start

        print("Function ran in %.6f seconds - output written to %s" % (
            duration, filepath))
        prof.dump_stats(filepath)

        print("Printing stats")
        stats = pstats.Stats(filepath)
        stats.sort_stats('cumulative')
        stats.print_stats()

        return result
    return profiled_fn
