
class Generator(object):
    """
    This class is the one that carries out with the Full report generation.
    """

    report_class = None
    formatter_class = None
    title = None

    def __init__(self, context={}, params={}):
        # context is passed to the formatter
        # params is passed to the form get_data
        self.context = context
        self.params = params
        self.formatter = self.formatter_class(self.context)

    def run(self):
        self.report = self.report_class()
        data = self.report.get_data(self.params)
        self.output_text = self.formatter.render(data)

