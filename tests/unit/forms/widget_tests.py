from oscar.forms import widgets


def compare_date_format(format, expected):
    assert widgets.datetime_format_to_js_date_format(format) == expected


def test_datetime_to_date_format_conversion():
    format_testcases = (
        ('%Y-%m-%d', 'yyyy-mm-dd'),
        ('%Y-%m-%d %H:%M', 'yyyy-mm-dd'),
    )
    for format, expected in format_testcases:
        yield compare_date_format, format, expected


def compare_time_format(format, expected):
    assert widgets.datetime_format_to_js_time_format(format) == expected


def test_datetime_to_time_format_conversion():
    format_testcases = (
        ('%Y-%m-%d %H:%M', 'hh:ii'),
        ('%H:%M', 'hh:ii'),
    )
    for format, expected in format_testcases:
        yield compare_time_format, format, expected
