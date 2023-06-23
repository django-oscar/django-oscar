from oscar.forms.widgets import datetime_format_to_js_input_mask


def test_js_input_mask():
    # Test all the possible input formats in one go
    fmt = "%Y-%m-%d %y %H:%M:%S %I"
    input_mask = datetime_format_to_js_input_mask(fmt)
    assert input_mask == "yyyy-mm-dd yy HH:MM:ss hh"
