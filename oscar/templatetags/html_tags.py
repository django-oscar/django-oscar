import re
from django.utils.safestring import mark_safe
from django import template
register = template.Library()

class_re = re.compile(r'(?<=class=["\'])(.*)(?=["\'])')


@register.filter
def add_class(value, css_class):
    """
    Add ``css_class`` on the html tag on wich the filter is applied.
    """
    string = unicode(value)
    match = class_re.search(string)
    if match:
        m = re.search(r'^%s$|^%s\s|\s%s\s|\s%s$' % (css_class, css_class,
                                                    css_class, css_class),
                      match.group(1))
        if not m:
            return mark_safe(class_re.sub(match.group(1) + " " + css_class,
                                          string))
    else:
        return mark_safe(string.replace('>', ' class="%s">' % css_class, 1))
    return value
