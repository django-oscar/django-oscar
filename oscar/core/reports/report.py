from .forms import DefaultForm


class Report(object):
    """
    A report to be generated has to validate the given input
    """

    data = []
    form_class = DefaultForm

    def get_form(self, *args, **kwargs):
        return self.form_class(*args, **kwargs)

    def __init__(self, params={}, **kwargs):
        self.params = params
        self.form = self.get_form(self.params)

    def get_data(self, params={}):
        "This is the method to be overriden"
        return self.data

