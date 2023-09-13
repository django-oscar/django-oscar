import sys


class temporary_python_path(object):
    """
    Acts as a context manager to temporarily prepend a list of paths to
    sys.path
    """

    def __init__(self, paths):
        self.paths = paths
        self.original_paths = sys.path[:]

    def __enter__(self):
        sys.path = self.paths + self.original_paths

    def __exit__(self, exc_type, exc_value, traceback):
        sys.path = self.original_paths


def delete_from_import_cache(module_name):
    """
    Deletes imported modules from the cache, so that they do not interfere with
    subsequent imports of different modules of the same names.

    Useful in situations where dynamically-created files are imported.
    """
    parts = module_name.split(".")
    for i, _ in enumerate(parts, 1):
        submodule_name = ".".join(parts[:i])
        del sys.modules[submodule_name]
