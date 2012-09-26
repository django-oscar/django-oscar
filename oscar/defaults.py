OSCAR_SHOP_NAME = 'Oscar'
OSCAR_SHOP_TAGLINE = 'Domain-driven e-Commerce for Django'

# Basket settings
OSCAR_BASKET_COOKIE_LIFETIME = 7 * 24 * 60 * 60
OSCAR_BASKET_COOKIE_OPEN = 'oscar_open_basket'
OSCAR_BASKET_COOKIE_SAVED = 'oscar_saved_basket'

# Currency
OSCAR_DEFAULT_CURRENCY = 'GBP'

# Max number of products to keep on the user's history
OSCAR_RECENTLY_VIEWED_PRODUCTS = 20

# Paths
OSCAR_IMAGE_FOLDER = 'images/products/%Y/%m/'
OSCAR_PROMOTION_FOLDER = 'images/promotions/'

# Copy this image from oscar/static/img to your MEDIA_ROOT folder.
# It needs to be there so Sorl can resize it.
OSCAR_MISSING_IMAGE_URL = 'image_not_found.jpg'
OSCAR_UPLOAD_ROOT = '/tmp'

# Search settings
OSCAR_SEARCH_SUGGEST_LIMIT = 10

# Checkout
OSCAR_ALLOW_ANON_CHECKOUT = False

# Partners
OSCAR_PARTNER_WRAPPERS = {}

# Promotions
COUNTDOWN, LIST, SINGLE_PRODUCT, TABBED_BLOCK = (
    'Countdown', 'List', 'SingleProduct', 'TabbedBlock')
OSCAR_PROMOTION_MERCHANDISING_BLOCK_TYPES = (
    (COUNTDOWN, "Vertical list"),
    (LIST, "Horizontal list"),
    (TABBED_BLOCK, "Tabbed block"),
    (SINGLE_PRODUCT, "Single product"),
)

# Reviews
OSCAR_ALLOW_ANON_REVIEWS = True
OSCAR_MODERATE_REVIEWS = False

# This enables sending alert notifications/emails
# instantly when products get back in stock
# by listening to stock record update signals
# this might impact performace for large numbers
# stock record updates.
# Alternatively, the management command
# ``oscar_send_alerts`` can be used to
# run periodically, e.g. as a cronjob. In this case
# instant alerts should be disabled.
OSCAR_EAGER_ALERTS = True

# Registration
OSCAR_SEND_REGISTRATION_EMAIL = True
OSCAR_FROM_EMAIL = 'oscar@example.com'

# Offers
OSCAR_OFFER_BLACKLIST_PRODUCT = None

# Max total number of items in basket
OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = None

# Cookies
OSCAR_COOKIES_DELETE_ON_LOGOUT = ['oscar_recently_viewed_products', ]

OSCAR_SETTINGS = dict(
    [(k, v) for k, v in locals().items() if k.startswith('OSCAR_')])
