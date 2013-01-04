from .forms import DefaultForm


class Report(object):
    """
    A report to be generated has to validate the given input
    """

    form_class = DefaultForm
    params = {}

    def get_data(self, params=None):
        "This is the method to be overriden"
        pass

