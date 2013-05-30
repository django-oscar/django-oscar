import nose

from oscar.forms import widgets


def test_datetime_to_date_format_conversion():
    format_testcases = (
        ('%Y-%m-%d', 'yy-mm-dd'),
        ('%Y-%m-%d %H:%M', 'yy-mm-dd'),
    )

    def compare(format, expected):
        nose.tools.eq_(
            widgets.datetime_format_to_js_date_format(format), expected)

    for format, expected in format_testcases:
        yield compare, format, expected


def test_datetime_to_time_format_conversion():
    format_testcases = (
        ('%Y-%m-%d', ''),
        ('%Y-%m-%d %H:%M', 'HH:mm'),
        ('%d/%m/%Y', ''),
    )

    def compare(format, expected):
        nose.tools.eq_(
            widgets.datetime_format_to_js_time_format(format), expected)

    for format, expected in format_testcases:
        yield compare, format, expected
