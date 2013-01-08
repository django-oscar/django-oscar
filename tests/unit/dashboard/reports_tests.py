import mock
from django.test import TestCase


class GeneratorTest(TestCase):
    """
    """

    def _get_test_class(self):
        from oscar.core.reports import Generator
        return Generator

    def _create_generator_object(self, **kwargs):
        return self._get_test_class()(**kwargs)

    def test_constructor_test(self):
        self._get_test_class()
        pass


class ReportTest(TestCase):
    """
    """

    def _get_test_class(self):
        from oscar.core.reports import Report
        return Report

    def test_constructor_calls_get_form_and_sets_params(self):
        params_dict = {'name': 'oscar'}
        with mock.patch('oscar.core.reports.Report.get_form') as get_form:
            report_class = self._get_test_class()
            report = report_class(params=params_dict)
            self.assertEqual(get_form.call_count, 1)
            get_form.assert_called_once_with(params_dict)
            self.assertEqual(report.params, params_dict)


class FormatterTest(TestCase):
    """
    """

    def _get_test_formatter_class(self):
        from oscar.core.reports.formatters import Formatter
        return Formatter

    def _get_test_paginated_formatter_class(self, _paginator_class, _paginated_by):
        formatter_klass = self._get_test_formatter_class()
        class PaginatedFormatter(formatter_klass):
            paginated_by = _paginated_by
            paginator_class = _paginator_class
        return PaginatedFormatter

    def test_get_data_chunk__returns_data_if_has_paginator_and_paginated_by(self):
        from django.core.paginator import Paginator
        formatter_class = self._get_test_paginated_formatter_class(Paginator, 2)
        formatter = formatter_class(context={})
        self.assertEqual(formatter.get_data_chunk([1, 2, 3, 4], 1), [1, 2])
        self.assertEqual(formatter.get_data_chunk([1, 2, 3, 4], 2), [3, 4])

    def test_get_data_chunk__returns_all_data_if_not_paginated(self):
        formatter_class = self._get_test_formatter_class()
        formatter = formatter_class()
        self.assertEqual(formatter.get_data_chunk([1, 2, 3]), [1, 2, 3])

