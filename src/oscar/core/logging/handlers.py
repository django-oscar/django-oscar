import os
from logging import FileHandler as BaseFileHandler


class EnvFileHandler(BaseFileHandler):
    """
    Custom filehandler that uses the LOG_ROOT setting to determine the folder
    to store log files in.

    We have to do some tricky stuff to avoid circular imports.  To this end,
    we pass /dev/null to the parent handler but specify opening to be delayed.
    Then when we try to first open the file, we join the LOG_ROOT with the
    passed filename.
    """

    def __init__(self, filename, *args, **kwargs):
        self.filename = filename
        kwargs['delay'] = True
        BaseFileHandler.__init__(self, "/dev/null", *args, **kwargs)

    def _open(self):
        # We import settings here to avoid a circular reference as this module
        # will be imported when settings.py is executed.
        from django.conf import settings
        self.baseFilename = os.path.join(settings.LOG_ROOT, self.filename)
        return BaseFileHandler._open(self)
