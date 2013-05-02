import sys


class temporary_python_path(object):
    """
    Acts as a context manager to temporarily prepend a list of paths to
    sys.path
    """
    def __init__(self, paths):
        self.paths = paths

    def __enter__(self):
        self.original_paths = sys.path[:]
        sys.path = self.paths + self.original_paths

    def __exit__(self, exc_type, exc_value, traceback):
        sys.path = self.original_paths
