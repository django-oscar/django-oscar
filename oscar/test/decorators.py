def dataProvider(fn_data_provider):
    """
    Data provider decorator, allows another callable to provide the data for the test.  
    This is a nice feature from PHPUnit which is very useful.  Am sticking with the JUnit style
    naming as unittest does this already.
    
    Implementation based on http://melp.nl/2011/02/phpunit-style-dataprovider-in-python-unit-test/#more-525
    """
    def test_decorator(test_method):
        def execute_test_method_with_each_data_set(self):
            for data in fn_data_provider():
                if len(data) == 2 and isinstance(data[0], tuple) and isinstance(data[1], dict):
                    # Both args and kwargs being provided
                    args, kwargs = data[:]
                else:
                    args, kwargs = data, {}
                try:
                    test_method(self, *args, **kwargs)
                except AssertionError, e:
                    self.fail("%s (Provided data: %s, %s)" % (e, args, kwargs))
        return execute_test_method_with_each_data_set
    return test_decorator