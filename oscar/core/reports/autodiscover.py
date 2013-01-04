import importlib
from django.conf import settings
from oscar.core.reports.generators import Generator
from django.template.defaultfilters import slugify

def _get_report_generator_map():
    report_map = {}

    for app in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module("%s.reports" % app)
        except ImportError:
            continue

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if not isinstance(attr, type):
                continue
            if issubclass(attr, Generator):
                if attr.title is not None:
                    report_map[slugify(attr.title)] = attr
    return report_map


