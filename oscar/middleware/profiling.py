import sys
import tempfile
import hotshot
import hotshot.stats
from cStringIO import StringIO

import cProfile
import pstats


class BaseMiddleware(object):
    query_param = None

    def show_profile(self, request):
        return self.query_param in request.GET

    def process_request(self, request):
        if self.show_profile(request):
            self.tmpfile = tempfile.NamedTemporaryFile()
            self.profile = self.profiler()

    def profiler(self):
        return None

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # We profile the view call - note that this misses the rest of Django's
        # request processing (eg middleware etc)
        if self.show_profile(request):
            return self.profile.runcall(
                callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if self.show_profile(request):
            stats = self.stats()

            # Capture STDOUT temporarily
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            if 'prof_strip' in request.GET:
                stats.strip_dirs()
            if 'prof_sort' in request.GET:
                stats.sort_stats(*request.GET['prof_sort'].split(','))
            else:
                stats.sort_stats('time', 'calls')
            stats.print_stats()
            stats_str = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = old_stdout

            # Print status within PRE block
            if response and response.content and stats_str:
                response.content = "<pre>" + stats_str + "</pre>"

        return response


class ProfileMiddleware(BaseMiddleware):
    query_param = 'cprofile'

    def profiler(self):
        return cProfile.Profile()

    def stats(self):
        self.profile.dump_stats(self.tmpfile.name)
        return pstats.Stats(self.tmpfile.name)


class HotshotMiddleware(BaseMiddleware):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Based on http://djangosnippets.org/snippets/186/
    """
    query_param = 'hotshot'

    def profiler(self):
        return hotshot.Profile(self.tmpfile.name)

    def stats(self):
        self.profile.close()
        return hotshot.stats.load(self.tmpfile.name)
