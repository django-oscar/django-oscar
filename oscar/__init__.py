import os

# Use 'final' as the 4th element to indicate
# a full release

VERSION = (0, 2, 2, 'final')
    
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


# Cheeky setting that can be used to override templates and give them
# the same name.  You can use:
#
# {% includes 'templates/basket/basket.html' %}
#
# when you want to create a new template with path 'basket/basket.html'
# Just add this setting to the end of your TEMPLATE_DIRS setting.
OSCAR_PARENT_TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))


OSCAR_CORE_APPS = [
    'oscar',
    'oscar.apps.analytics',
    'oscar.apps.order',
    'oscar.apps.checkout',
    'oscar.apps.shipping',
    'oscar.apps.catalogue',
    'oscar.apps.catalogue.reviews',
    'oscar.apps.basket',
    'oscar.apps.payment',
    'oscar.apps.offer',
    'oscar.apps.address',
    'oscar.apps.partner',
    'oscar.apps.customer',
    'oscar.apps.promotions',
    'oscar.apps.search',
    'oscar.apps.voucher',
    'oscar.apps.dashboard',
    'oscar.apps.dashboard.reports',
    'oscar.apps.dashboard.users',
    'oscar.apps.dashboard.orders',
    'oscar.apps.dashboard.promotions',
    'oscar.apps.dashboard.catalogue',
    'oscar.apps.dashboard.offers',
    'oscar.apps.dashboard.ranges',
    'oscar.apps.dashboard.vouchers',
]


def get_core_apps(overrides=None):
    """
    Return a list of oscar's apps amended with any passed overrides
    """
    if overrides is None:
        return OSCAR_CORE_APPS
    def get_app_label(app_label, overrides):
        pattern = app_label.replace('oscar.apps.', '')
        for override in overrides:
            if override.endswith(pattern):
                return override
        return app_label

    apps = []
    for app_label in OSCAR_CORE_APPS:
        apps.append(get_app_label(app_label, overrides))
    return apps





    return OSCAR_CORE_APPS
