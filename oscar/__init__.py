import os

# Use 'final' as the 4th element to indicate
# a full release

VERSION = (0, 6, 0, 'alpha', 0)


def get_short_version():
    return '%s.%s' % (VERSION[0], VERSION[1])


def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        # Append 3rd digit if > 0
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    elif VERSION[3] != 'final':
        version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    return version


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
    'oscar.apps.catalogue.reviews',
    'oscar.apps.partner',
    'oscar.apps.basket',
    'oscar.apps.payment',
    'oscar.apps.offer',
    'oscar.apps.order',
    'oscar.apps.customer',
    'oscar.apps.promotions',
    'oscar.apps.search',
    'oscar.apps.voucher',
    'oscar.apps.wishlists',
    'oscar.apps.dashboard',
    'oscar.apps.dashboard.reports',
    'oscar.apps.dashboard.users',
    'oscar.apps.dashboard.orders',
    'oscar.apps.dashboard.promotions',
    'oscar.apps.dashboard.catalogue',
    'oscar.apps.dashboard.offers',
    'oscar.apps.dashboard.partners',
    'oscar.apps.dashboard.pages',
    'oscar.apps.dashboard.ranges',
    'oscar.apps.dashboard.reviews',
    'oscar.apps.dashboard.vouchers',
    'oscar.apps.dashboard.communications',
    # 3rd-party apps that oscar depends on
    'haystack',
    'treebeard',
    'sorl.thumbnail',
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
