import nose

from oscar.forms import widgets


def compare_date_format(format, expected):
    nose.tools.eq_(
        widgets.datetime_format_to_js_date_format(format), expected)


def test_datetime_to_date_format_conversion():
    format_testcases = (
        ('%Y-%m-%d', 'yy-mm-dd'),
        ('%Y-%m-%d %H:%M', 'yy-mm-dd'),
    )
    for format, expected in format_testcases:
        yield compare_date_format, format, expected


def compare_time_format(format, expected):
    nose.tools.eq_(
        widgets.datetime_format_to_js_time_format(format), expected)


def test_datetime_to_time_format_conversion():
    format_testcases = (
        ('%Y-%m-%d', ''),
        ('%Y-%m-%d %H:%M', 'HH:mm'),
        ('%d/%m/%Y', ''),
    )
    for format, expected in format_testcases:
        yield compare_time_format, format, expected
