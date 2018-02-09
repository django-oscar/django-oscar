from pydoc import locate

from django.conf import settings


class AnalyzerRegistry(object):

    def __init__(self):
        self.analyzers = {}

    def define_in_index(self, index):
        for analyzer_path in settings.OSCAR_SEARCH['ANALYZERS']:
            analyzer = locate(analyzer_path)
            if not analyzer:
                raise ImportError('{} not found'.format(analyzer_path))

            analyzer_name = analyzer._name
            if analyzer_name in self.analyzers:
                raise KeyError("Analyzer with name {} registered twice, please remove one".format(analyzer_name))

            self.analyzers[analyzer_name] = analyzer

        for analyzer in self.analyzers.values():
            index.analyzer(analyzer)
