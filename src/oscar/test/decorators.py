import warnings
from functools import wraps

import mock

from oscar.utils.deprecation import RemovedInOscar15Warning


def dataProvider(fn_data_provider):
    """
    Data provider decorator, allows another callable to provide the data for
    the test.  This is a nice feature from PHPUnit which is very useful.  Am
    sticking with the JUnit style naming as unittest does this already.

    Implementation based on:
    http://melp.nl/2011/02/phpunit-style-dataprovider-in-python-unit-test/#more-525  # noqa
    """

    warnings.warn(
        "dataProvider() is deprecated and will be removed in Oscar 1.5",
        RemovedInOscar15Warning)

    def test_decorator(test_method):
        def execute_test_method_with_each_data_set(self):
            for data in fn_data_provider():
                if (len(data) == 2 and isinstance(data[0], tuple) and
                        isinstance(data[1], dict)):
                    # Both args and kwargs being provided
                    args, kwargs = data[:]
                else:
                    args, kwargs = data, {}
                try:
                    test_method(self, *args, **kwargs)
                except AssertionError as e:
                    self.fail("%s (Provided data: %s, %s)" % (e, args, kwargs))
        return execute_test_method_with_each_data_set
    return test_decorator


# This will be in Oscar 0.6 - it should be functools though!
def compose(*functions):
    """
    Compose functions

    This is useful for combining decorators.
    """
    warnings.warn(
        "compose() is deprecated and will be removed in Oscar 1.5",
        RemovedInOscar15Warning)

    def _composed(*args):
        for fn in functions:
            try:
                args = fn(*args)
            except TypeError:
                # args must be scalar so we don't try to expand it
                args = fn(args)
        return args
    return _composed


no_database = mock.patch(
    'django.db.backends.util.CursorWrapper', mock.Mock(
        side_effect=RuntimeError("Using the database is not permitted!")))


no_filesystem = mock.patch('__builtin__.open', mock.Mock(
    side_effect=RuntimeError("Using the filesystem is not permitted!")))


no_sockets = mock.patch('socket.getaddrinfo', mock.Mock(
    side_effect=RuntimeError("Using sockets is not permitted!")))


no_externals = no_diggity = compose(
    no_database, no_filesystem, no_sockets)  # = no doubt


def ignore_deprecation_warnings(target):
    """
    Ignore deprecation warnings for the wrapped TestCase or test method

    This is useful as the test runner can be set to raise an exception on a
    deprecation warning.  Using this decorator allows tests to exercise
    deprecated code without an exception.
    """
    warnings.warn(
        "ignore_deprecation_warnings() is deprecated and will be " +
        "removed in Oscar 1.5",
        RemovedInOscar15Warning)

    if target.__class__.__name__ not in ('instancemethod', 'function'):
        # Decorate every test method in class
        for attr in dir(target):
            if not attr.startswith('test'):
                continue
            attr_value = getattr(target, attr)
            if not hasattr(attr_value, '__call__'):
                continue
            setattr(target, attr, ignore_deprecation_warnings(attr_value))
        return target
    else:
        # Decorate single test method
        @wraps(target)
        def _wrapped(*args, **kwargs):
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                return target(*args, **kwargs)
        return _wrapped
