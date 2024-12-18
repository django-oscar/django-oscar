from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

OSCAR_SHOP_NAME = ""
OSCAR_SHOP_TAGLINE = ""
OSCAR_HOMEPAGE = reverse_lazy("catalogue:index")

# Dynamic class loading
OSCAR_DYNAMIC_CLASS_LOADER = "oscar.core.loading.default_class_loader"

# Basket settings
OSCAR_BASKET_COOKIE_LIFETIME = 7 * 24 * 60 * 60
OSCAR_BASKET_COOKIE_OPEN = "oscar_open_basket"
OSCAR_BASKET_COOKIE_SECURE = False
OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = 10000

# Recently-viewed products
OSCAR_RECENTLY_VIEWED_COOKIE_LIFETIME = 7 * 24 * 60 * 60
OSCAR_RECENTLY_VIEWED_COOKIE_NAME = "oscar_history"
OSCAR_RECENTLY_VIEWED_COOKIE_SECURE = False
OSCAR_RECENTLY_VIEWED_PRODUCTS = 20

# Currency
OSCAR_DEFAULT_CURRENCY = "GBP"

# Paths
OSCAR_IMAGE_FOLDER = "images/products/%Y/%m/"
OSCAR_DELETE_IMAGE_FILES = True

# Copy this image from oscar/static/img to your MEDIA_ROOT folder.
# It needs to be there so Sorl can resize it.
OSCAR_MISSING_IMAGE_URL = "image_not_found.jpg"

# Address settings
OSCAR_REQUIRED_ADDRESS_FIELDS = (
    "first_name",
    "last_name",
    "line1",
    "line4",
    "postcode",
    "country",
)

# Pagination settings

OSCAR_OFFERS_PER_PAGE = 20
OSCAR_PRODUCTS_PER_PAGE = 20
OSCAR_REVIEWS_PER_PAGE = 20
OSCAR_NOTIFICATIONS_PER_PAGE = 20
OSCAR_EMAILS_PER_PAGE = 20
OSCAR_ORDERS_PER_PAGE = 20
OSCAR_ADDRESSES_PER_PAGE = 20
OSCAR_STOCK_ALERTS_PER_PAGE = 20
OSCAR_DASHBOARD_ITEMS_PER_PAGE = 20

# Checkout
OSCAR_ALLOW_ANON_CHECKOUT = False

# Reviews
OSCAR_ALLOW_ANON_REVIEWS = True
OSCAR_MODERATE_REVIEWS = False

# Accounts
OSCAR_ACCOUNTS_REDIRECT_URL = "customer:profile-view"

# This enables sending alert notifications/emails instantly when products get
# back in stock by listening to stock record update signals.
# This might impact performance for large numbers of stock record updates.
# Alternatively, the management command ``oscar_send_alerts`` can be used to
# run periodically, e.g. as a cron job. In this case eager alerts should be
# disabled.
OSCAR_EAGER_ALERTS = True

# Registration
OSCAR_SEND_REGISTRATION_EMAIL = True
OSCAR_FROM_EMAIL = "oscar@example.com"

# Slug handling
OSCAR_SLUG_FUNCTION = "oscar.core.utils.default_slugifier"
OSCAR_SLUG_MAP = {}
OSCAR_SLUG_BLACKLIST = []
OSCAR_SLUG_ALLOW_UNICODE = False

# Cookies
OSCAR_COOKIES_DELETE_ON_LOGOUT = [
    "oscar_recently_viewed_products",
]

# Offers
OSCAR_OFFERS_INCL_TAX = False
# Values (using the names of the model constants) from
# "offer.ConditionalOffer.TYPE_CHOICES"
OSCAR_OFFERS_IMPLEMENTED_TYPES = [
    "SITE",
    "VOUCHER",
]

# Hidden Oscar features, e.g. wishlists or reviews
OSCAR_HIDDEN_FEATURES = []

# Menu structure of the dashboard navigation
OSCAR_DASHBOARD_NAVIGATION = [
    {
        "label": _("Dashboard"),
       "icon": '''
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path fill-rule="evenodd" clip-rule="evenodd" d="M12 1.25C6.06294 1.25 1.25 6.06294 1.25 12C1.25 17.9371 6.06294 22.75 12 22.75C17.9371 22.75 22.75 17.9371 22.75 12C22.75 6.06294 17.9371 1.25 12 1.25ZM12 3.25C12.4142 3.25 12.75 3.58579 12.75 4V5.3C12.75 5.71421 12.4142 6.05 12 6.05C11.5858 6.05 11.25 5.71421 11.25 5.3V4C11.25 3.58579 11.5858 3.25 12 3.25ZM6.12967 6.07642C6.41883 5.77985 6.89366 5.77384 7.19024 6.063L8.07913 6.92967C8.37571 7.21883 8.38172 7.69366 8.09255 7.99024C7.80339 8.28682 7.32856 8.29283 7.03198 8.00367L6.14309 7.137C5.84651 6.84784 5.8405 6.373 6.12967 6.07642ZM17.8703 6.07642C18.1595 6.373 18.1535 6.84784 17.8569 7.137L16.968 8.00367C16.6714 8.29283 16.1966 8.28682 15.9074 7.99024C15.6183 7.69366 15.6243 7.21883 15.9209 6.92967L16.8098 6.063C17.1063 5.77384 17.5812 5.77985 17.8703 6.07642ZM3.25 11.8C3.25 11.3858 3.58579 11.05 4 11.05H5.33333C5.74755 11.05 6.08333 11.3858 6.08333 11.8C6.08333 12.2142 5.74755 12.55 5.33333 12.55H4C3.58579 12.55 3.25 12.2142 3.25 11.8ZM17.9167 11.8C17.9167 11.3858 18.2525 11.05 18.6667 11.05L20 11.05C20.4142 11.05 20.75 11.3858 20.75 11.8C20.75 12.2142 20.4142 12.55 20 12.55L18.6667 12.55C18.2525 12.55 17.9167 12.2142 17.9167 11.8ZM8.09298 15.6099C8.38209 15.9065 8.37599 16.3813 8.07936 16.6704L7.19014 17.5371C6.89351 17.8262 6.41868 17.8201 6.12957 17.5235C5.84046 17.2268 5.84656 16.752 6.14319 16.4629L7.0324 15.5962C7.32903 15.3071 7.80387 15.3132 8.09298 15.6099ZM15.9074 15.6098C16.1966 15.3132 16.6714 15.3072 16.968 15.5963L17.8569 16.463C18.1535 16.7522 18.1595 17.227 17.8703 17.5236C17.5812 17.8202 17.1063 17.8262 16.8098 17.537L15.9209 16.6703C15.6243 16.3812 15.6183 15.9063 15.9074 15.6098ZM10 12.5556C10 15.8148 14 15.8148 14 12.5556C14 11.1148 13.0349 9.96 12.4455 9.38909C12.3241 9.27151 12.2634 9.21271 12.1514 9.17711C12.07 9.15122 11.9299 9.15122 11.8485 9.17712C11.7365 9.21272 11.6758 9.27152 11.5544 9.38911C10.965 9.96002 10 11.1148 10 12.5556Z" fill="#FF2E00"/>
            </svg>
        ''',
        "url_name": "dashboard:index",
    },
    {
        "label": _("Catalogue"),
        "icon": '''
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 6C10 8.20914 8.20914 10 6 10C3.79086 10 2 8.20914 2 6C2 3.79086 3.79086 2 6 2C8.20914 2 10 3.79086 10 6Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M22 6C22 8.20914 20.2091 10 18 10C15.7909 10 14 8.20914 14 6C14 3.79086 15.7909 2 18 2C20.2091 2 22 3.79086 22 6Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M22 18C22 20.2091 20.2091 22 18 22C15.7909 22 14 20.2091 14 18C14 15.7909 15.7909 14 18 14C20.2091 14 22 15.7909 22 18Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M10 18C10 20.2091 8.20914 22 6 22C3.79086 22 2 20.2091 2 18C2 15.7909 3.79086 14 6 14C8.20914 14 10 15.7909 10 18Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                 ''',
        "children": [
            {
                "label": _("Products"),
                "url_name": "dashboard:catalogue-product-list",
            },
            {
                "label": _("Product Types"),
                "url_name": "dashboard:catalogue-class-list",
            },
            {
                "label": _("Categories"),
                "url_name": "dashboard:catalogue-category-list",
            },
            {
                "label": _("Ranges"),
                "url_name": "dashboard:range-list",
            },
            {
                "label": _("Low stock alerts"),
                "url_name": "dashboard:stock-alert-list",
            },
            {
                "label": _("Options"),
                "url_name": "dashboard:catalogue-option-list",
            },
            {
                "label": _("Attribute Option Groups"),
                "url_name": "dashboard:catalogue-attribute-option-group-list",
            },
        ],
    },
    {
        "label": _("Fulfilment"),
        "icon": '''
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M2 12C2 16.9706 6 22 12 22C18 22 22 18 22 12C22 6 18 2 12 2C6 2 2 7 2 7M2 7V3M2 7H5.5M12 8V12L15 14" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>

                 ''',
        "children": [
            {
                "label": _("Orders"),
                "url_name": "dashboard:order-list",
            },
            {
                "label": _("Statistics"),
                "url_name": "dashboard:order-stats",
            },
            {
                "label": _("Partners"),
                "url_name": "dashboard:partner-list",
            },
            # The shipping method dashboard is disabled by default as it might
            # be confusing. Weight-based shipping methods aren't hooked into
            # the shipping repository by default (as it would make
            # customising the repository slightly more difficult).
            # {
            #     'label': _('Shipping charges'),
            #     'url_name': 'dashboard:shipping-method-list',
            # },
        ],
    },
    {
        "label": _("Customers"),
        "icon": '''
                 <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M15 10C17.2091 10 19 8.20914 19 6C19 3.79086 17.2091 2 15 2M17 22H19.8C21.5673 22 23 20.5673 23 18.8V18.8C23 16.149 20.851 14 18.2 14H17M12 6C12 8.20914 10.2091 10 8 10C5.79086 10 4 8.20914 4 6C4 3.79086 5.79086 2 8 2C10.2091 2 12 3.79086 12 6ZM4.2 22H11.8C13.5673 22 15 20.5673 15 18.8V18.8C15 16.149 12.851 14 10.2 14H5.8C3.14903 14 1 16.149 1 18.8V18.8C1 20.5673 2.43269 22 4.2 22Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>

                 ''',
        "children": [
            {
                "label": _("Customers"),
                "url_name": "dashboard:users-index",
            },
            {
                "label": _("Stock alert requests"),
                "url_name": "dashboard:user-alert-list",
            },
        ],
    },
    {
        "label": _("Offers"),
       "icon": '''
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M5.50049 10.5L2.00049 7.9999L3.07849 6.92193C3.964 6.03644 4.40676 5.5937 4.9307 5.31387C5.39454 5.06614 5.90267 4.91229 6.42603 4.86114C7.01719 4.80336 7.63117 4.92617 8.85913 5.17177L10.5 5.49997M18.4999 13.5L18.8284 15.1408C19.0742 16.3689 19.1971 16.983 19.1394 17.5743C19.0883 18.0977 18.9344 18.6059 18.6867 19.0699C18.4068 19.5939 17.964 20.0367 17.0783 20.9224L16.0007 22L13.5007 18.5M7 16.9998L8.99985 15M17.0024 8.99951C17.0024 10.1041 16.107 10.9995 15.0024 10.9995C13.8979 10.9995 13.0024 10.1041 13.0024 8.99951C13.0024 7.89494 13.8979 6.99951 15.0024 6.99951C16.107 6.99951 17.0024 7.89494 17.0024 8.99951ZM17.1991 2H16.6503C15.6718 2 15.1826 2 14.7223 2.11053C14.3141 2.20853 13.9239 2.37016 13.566 2.5895C13.1623 2.83689 12.8164 3.18282 12.1246 3.87469L6.99969 9C5.90927 10.0905 5.36406 10.6358 5.07261 11.2239C4.5181 12.343 4.51812 13.6569 5.07268 14.776C5.36415 15.3642 5.90938 15.9094 6.99984 16.9998V16.9998C8.09038 18.0904 8.63565 18.6357 9.22386 18.9271C10.343 19.4817 11.6569 19.4817 12.7761 18.9271C13.3643 18.6356 13.9095 18.0903 15 16.9997L20.1248 11.8745C20.8165 11.1827 21.1624 10.8368 21.4098 10.4331C21.6291 10.0753 21.7907 9.6851 21.8886 9.27697C21.9991 8.81664 21.9991 8.32749 21.9991 7.34918V6.8C21.9991 5.11984 21.9991 4.27976 21.6722 3.63803C21.3845 3.07354 20.9256 2.6146 20.3611 2.32698C19.7194 2 18.8793 2 17.1991 2Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>


                 ''',
        "children": [
            {
                "label": _("Offers"),
                "url_name": "dashboard:offer-list",
            },
            {
                "label": _("Vouchers"),
                "url_name": "dashboard:voucher-list",
            },
            {
                "label": _("Voucher Sets"),
                "url_name": "dashboard:voucher-set-list",
            },
        ],
    },
    {
        "label": _("Content"),
       "icon": '''
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M2 6.8C2 5.11984 2 4.27976 2.32698 3.63803C2.6146 3.07354 3.07354 2.6146 3.63803 2.32698C4.27976 2 5.11984 2 6.8 2H8.31672C9.11834 2 9.51916 2 9.88103 2.09146C10.4791 2.24262 11.016 2.57444 11.4186 3.04174C11.6623 3.32451 11.8415 3.683 12.2 4.4V4.4C12.439 4.878 12.5585 5.11699 12.7209 5.30551C12.9894 5.61704 13.3473 5.83825 13.746 5.93902C13.9872 6 14.2544 6 14.7889 6H15.6C17.8402 6 18.9603 6 19.816 6.43597C20.5686 6.81947 21.1805 7.43139 21.564 8.18404C22 9.03968 22 10.1598 22 12.4V15.6C22 17.8402 22 18.9603 21.564 19.816C21.1805 20.5686 20.5686 21.1805 19.816 21.564C18.9603 22 17.8402 22 15.6 22H8.4C6.15979 22 5.03968 22 4.18404 21.564C3.43139 21.1805 2.81947 20.5686 2.43597 19.816C2 18.9603 2 17.8402 2 15.6V6.8Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>


                 ''',
        "children": [
            {
                "label": _("Pages"),
                "url_name": "dashboard:page-list",
            },
            {
                "label": _("Email templates"),
                "url_name": "dashboard:comms-list",
            },
            {
                "label": _("Reviews"),
                "url_name": "dashboard:reviews-list",
            },
        ],
    },
    {
        "label": _("Reports"),
        "icon": '''
               <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 8H14M8 12H16M8 16H12M10 22H14C16.8003 22 18.2004 22 19.27 21.455C20.2108 20.9757 20.9757 20.2108 21.455 19.27C22 18.2004 22 16.8003 22 14V10C22 7.19974 22 5.79961 21.455 4.73005C20.9757 3.78924 20.2108 3.02433 19.27 2.54497C18.2004 2 16.8003 2 14 2H10C7.19974 2 5.79961 2 4.73005 2.54497C3.78924 3.02433 3.02433 3.78924 2.54497 4.73005C2 5.79961 2 7.19974 2 10V14C2 16.8003 2 18.2004 2.54497 19.27C3.02433 20.2108 3.78924 20.9757 4.73005 21.455C5.79961 22 7.19974 22 10 22Z" stroke="black" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>

                 ''',
        "url_name": "dashboard:reports-index",
    },
]
OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION = "oscar.apps.dashboard.nav.default_access_fn"

# Search facets
OSCAR_SEARCH_FACETS = {
    "fields": {
        # The key for these dicts will be used when passing facet data
        # to the template. Same for the 'queries' dict below.
        "product_class": {"name": _("Type"), "field": "product_class"},
        "rating": {"name": _("Rating"), "field": "rating"},
        # You can specify an 'options' element that will be passed to the
        # SearchQuerySet.facet() call.
        # For instance, with Elasticsearch backend, 'options': {'order': 'term'}
        # will sort items in a facet by title instead of number of items.
        # It's hard to get 'missing' to work
        # correctly though as of Solr's hilarious syntax for selecting
        # items without a specific facet:
        # http://wiki.apache.org/solr/SimpleFacetParameters#facet.method
        # 'options': {'missing': 'true'}
    },
    "queries": {
        "price_range": {
            "name": _("Price range"),
            "field": "price",
            "queries": [
                # This is a list of (name, query) tuples where the name will
                # be displayed on the front-end.
                (_("0 to 20"), "[0 TO 20]"),
                (_("20 to 40"), "[20 TO 40]"),
                (_("40 to 60"), "[40 TO 60]"),
                (_("60+"), "[60 TO *]"),
            ],
        },
    },
}

OSCAR_THUMBNAILER = "oscar.core.thumbnails.SorlThumbnail"

OSCAR_URL_SCHEMA = "http"

OSCAR_SAVE_SENT_EMAILS_TO_DB = True

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"
