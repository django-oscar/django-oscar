from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

OSCAR_SHOP_NAME = 'Oscar'
OSCAR_SHOP_TAGLINE = ''
OSCAR_HOMEPAGE = reverse_lazy('promotions:home')

# Basket settings
OSCAR_BASKET_COOKIE_LIFETIME = 7 * 24 * 60 * 60
OSCAR_BASKET_COOKIE_OPEN = 'oscar_open_basket'
OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = 10000

# Recently-viewed products
OSCAR_RECENTLY_VIEWED_COOKIE_LIFETIME = 7 * 24 * 60 * 60
OSCAR_RECENTLY_VIEWED_COOKIE_NAME = 'oscar_history'
OSCAR_RECENTLY_VIEWED_PRODUCTS = 20

# Currency
OSCAR_DEFAULT_CURRENCY = 'GBP'

# Paths
OSCAR_IMAGE_FOLDER = 'images/products/%Y/%m/'
OSCAR_PROMOTION_FOLDER = 'images/promotions/'
OSCAR_DELETE_IMAGE_FILES = True

# Copy this image from oscar/static/img to your MEDIA_ROOT folder.
# It needs to be there so Sorl can resize it.
OSCAR_MISSING_IMAGE_URL = 'image_not_found.jpg'
OSCAR_UPLOAD_ROOT = '/tmp'

# Address settings
OSCAR_REQUIRED_ADDRESS_FIELDS = ('first_name', 'last_name', 'line1',
                                 'line4', 'postcode', 'country')

# Product list settings
OSCAR_PRODUCTS_PER_PAGE = 20

# Checkout
OSCAR_ALLOW_ANON_CHECKOUT = False

# Promotions
COUNTDOWN, LIST, SINGLE_PRODUCT, TABBED_BLOCK = (
    'Countdown', 'List', 'SingleProduct', 'TabbedBlock')
OSCAR_PROMOTION_MERCHANDISING_BLOCK_TYPES = (
    (COUNTDOWN, "Vertical list"),
    (LIST, "Horizontal list"),
    (TABBED_BLOCK, "Tabbed block"),
    (SINGLE_PRODUCT, "Single product"),
)
OSCAR_PROMOTION_POSITIONS = (('page', 'Page'),
                             ('right', 'Right-hand sidebar'),
                             ('left', 'Left-hand sidebar'))

# Reviews
OSCAR_ALLOW_ANON_REVIEWS = True
OSCAR_MODERATE_REVIEWS = False

# Accounts
OSCAR_ACCOUNTS_REDIRECT_URL = 'customer:profile-view'

# This enables sending alert notifications/emails instantly when products get
# back in stock by listening to stock record update signals.
# This might impact performance for large numbers of stock record updates.
# Alternatively, the management command ``oscar_send_alerts`` can be used to
# run periodically, e.g. as a cron job. In this case eager alerts should be
# disabled.
OSCAR_EAGER_ALERTS = True

# Registration
OSCAR_SEND_REGISTRATION_EMAIL = True
OSCAR_FROM_EMAIL = 'oscar@example.com'

# Slug handling
OSCAR_SLUG_FUNCTION = 'oscar.core.utils.default_slugifier'
OSCAR_SLUG_MAP = {}
OSCAR_SLUG_BLACKLIST = []

# Cookies
OSCAR_COOKIES_DELETE_ON_LOGOUT = ['oscar_recently_viewed_products', ]

# Hidden Oscar features, e.g. wishlists or reviews
OSCAR_HIDDEN_FEATURES = []

# Menu structure of the dashboard navigation
OSCAR_DASHBOARD_NAVIGATION = {
    'index': {
        'label': _('Dashboard'),
        'icon': 'icon-th-list',
        'url_name': 'dashboard:index',
        'order': 1,
    },
    'catalogue': {
        'label': _('Catalogue'),
        'icon': 'icon-sitemap',
        'order': 2,
        'children': {
            'products': {
                'label': _('Products'),
                'url_name': 'dashboard:catalogue-product-list',
                'order': 1,
            },
            'product_types': {
                'label': _('Product Types'),
                'url_name': 'dashboard:catalogue-class-list',
                'order': 2,
            },
            'categories': {
                'label': _('Categories'),
                'url_name': 'dashboard:catalogue-category-list',
                'order': 3,
            },
            'ranges': {
                'label': _('Ranges'),
                'url_name': 'dashboard:range-list',
                'order': 4,
            },
            'stock_alerts': {
                'label': _('Low stock alerts'),
                'url_name': 'dashboard:stock-alert-list',
                'order': 5,
            },
        }
    },
    'fulfilment': {
        'label': _('Fulfilment'),
        'icon': 'icon-shopping-cart',
        'order': 3,
        'children': {
            'orders': {
                'label': _('Orders'),
                'url_name': 'dashboard:order-list',
                'order': 1,
            },
            'statistics': {
                'label': _('Statistics'),
                'url_name': 'dashboard:order-stats',
                'order': 2,
            },
            'partners': {
                'label': _('Partners'),
                'url_name': 'dashboard:partner-list',
                'order': 3,
            },
            # The shipping method dashboard is disabled by default as it might
            # be confusing. Weight-based shipping methods aren't hooked into
            # the shipping repository by default (as it would make
            # customising the repository slightly more difficult).
            # {
            #     'label': _('Shipping charges'),
            #     'url_name': 'dashboard:shipping-method-list',
            # },
        }
    },
    'customers': {
        'label': _('Customers'),
        'icon': 'icon-group',
        'order': 4,
        'children': {
            'customers': {
                'label': _('Customers'),
                'url_name': 'dashboard:users-index',
                'order': 1,
            },
            'stock_alerts': {
                'label': _('Stock alert requests'),
                'url_name': 'dashboard:user-alert-list',
                'order': 2,
            },
        }
    },
    'offers': {
        'label': _('Offers'),
        'icon': 'icon-bullhorn',
        'order': 5,
        'children': {
            'offers': {
                'label': _('Offers'),
                'url_name': 'dashboard:offer-list',
                'order': 1,
            },
            'vouchers': {
                'label': _('Vouchers'),
                'url_name': 'dashboard:voucher-list',
                'order': 2,
            },
        },
    },
    'content': {
        'label': _('Content'),
        'icon': 'icon-folder-close',
        'order': 6,
        'children': {
            'content_blocks': {
                'label': _('Content blocks'),
                'url_name': 'dashboard:promotion-list',
                'order': 1,
            },
            'content_blocks_by_page': {
                'label': _('Content blocks by page'),
                'url_name': 'dashboard:promotion-list-by-page',
                'order': 2,
            },
            'pages': {
                'label': _('Pages'),
                'url_name': 'dashboard:page-list',
                'order': 3,
            },
            'email_templates': {
                'label': _('Email templates'),
                'url_name': 'dashboard:comms-list',
                'order': 4,
            },
            'reviews': {
                'label': _('Reviews'),
                'url_name': 'dashboard:reviews-list',
                'order': 5,
            },
        }
    },
    'reports': {
        'label': _('Reports'),
        'icon': 'icon-bar-chart',
        'url_name': 'dashboard:reports-index',
        'order': 7,
    },
}
OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION = 'oscar.apps.dashboard.nav.default_access_fn'  # noqa

# Search facets
OSCAR_SEARCH_FACETS = {
    'fields': {
        # The key for these dicts will be used when passing facet data
        # to the template. Same for the 'queries' dict below.
        'product_class': {
            'name': _('Type'),
            'field': 'product_class'
        },
        'rating': {
            'name': _('Rating'),
            'field': 'rating',
            # You can specify an 'options' element that will be passed to the
            # SearchQuerySet.facet() call.  It's hard to get 'missing' to work
            # correctly though as of Solr's hilarious syntax for selecting
            # items without a specific facet:
            # http://wiki.apache.org/solr/SimpleFacetParameters#facet.method
            # 'options': {'missing': 'true'}
        }
    },
    'queries': {
        'price_range': {
            'name': _('Price range'),
            'field': 'price',
            'queries': [
                # This is a list of (name, query) tuples where the name will
                # be displayed on the front-end.
                (_('0 to 20'), u'[0 TO 20]'),
                (_('20 to 40'), u'[20 TO 40]'),
                (_('40 to 60'), u'[40 TO 60]'),
                (_('60+'), u'[60 TO *]'),
            ]
        },
    }
}

OSCAR_SETTINGS = dict(
    [(k, v) for k, v in locals().items() if k.startswith('OSCAR_')])
