import warnings


def deprecated(f):
    def _deprecated(*args, **kwargs):
        message = "Method '%s' is deprecated and will be " \
            "removed in the next major version of django-oscar" \
            % f.__name__
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return f(*args, **kwargs)
    return _deprecated
