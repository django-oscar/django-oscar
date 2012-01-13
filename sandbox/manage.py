#!/usr/bin/env python
from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    try:
        execute_manager(settings)
    except Exception, e:
        # Custom handling of exceptions to make sure
        # that Sentry handles them.
        import sys, traceback
        if sys.stdout.isatty():
            traceback.print_exc()
        else:
            if settings.DEBUG or not 'sentry.client' in settings.INSTALLED_APPS:
                raise
            from sentry.client.models import get_client
            exc_info = sys.exc_info()
            if getattr(exc_info[0], 'skip_sentry', False):
                raise
            get_client().create_from_exception(exc_info)
            
            # Email admins
            import logging
            logger = logging.getLogger('management_commands')
            logger.exception(e)
