import os

# Use 'dev', 'beta', or 'final' as the 4th element to indicate release type.

VERSION = (1, 0, 1, 'machtfit', 40)


def get_short_version():
    return '%s.%s' % (VERSION[0], VERSION[1])


def get_version():
    return '{}.{}.{}-{}-{}'.format(*VERSION)


# Cheeky setting that allows each template to be accessible by two paths.
# Eg: the template 'oscar/templates/oscar/base.html' can be accessed via both
# 'base.html' and 'oscar/base.html'.  This allows Oscar's templates to be
# extended by templates with the same filename
OSCAR_MAIN_TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'templates/oscar')

OSCAR_CORE_APPS = [
    'oscar',
    'oscar.apps.analytics',
    'oscar.apps.checkout',
    'oscar.apps.address',
    'oscar.apps.shipping',
    'oscar.apps.catalogue',
    'oscar.apps.partner',
    'oscar.apps.basket',
    'oscar.apps.payment',
    'oscar.apps.offer',
    'oscar.apps.order',
    'oscar.apps.customer',
    'oscar.apps.voucher',
    'oscar.apps.dashboard',
    'oscar.apps.dashboard.reports',
    'oscar.apps.dashboard.users',
    'oscar.apps.dashboard.orders',
    'oscar.apps.dashboard.catalogue',
    'oscar.apps.dashboard.offers',
    'oscar.apps.dashboard.partners',
    'oscar.apps.dashboard.ranges',
    # 3rd-party apps that oscar depends on
    'treebeard',
    'sorl.thumbnail',
    'django_tables2',
]


def get_core_apps(overrides=None):
    """
    Return a list of oscar's apps amended with any passed overrides
    """
    if not overrides:
        return OSCAR_CORE_APPS

    def get_app_label(app_label, overrides):
        pattern = app_label.replace('oscar.apps.', '')
        for override in overrides:
            if override.endswith(pattern):
                if 'dashboard' in override and 'dashboard' not in pattern:
                    continue
                return override
        return app_label

    apps = []
    for app_label in OSCAR_CORE_APPS:
        apps.append(get_app_label(app_label, overrides))
    return apps
