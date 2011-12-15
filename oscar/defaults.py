# Basket settings
OSCAR_BASKET_COOKIE_LIFETIME = 7*24*60*60
OSCAR_BASKET_COOKIE_OPEN = 'oscar_open_basket'
OSCAR_BASKET_COOKIE_SAVED = 'oscar_saved_basket'

# Currency
OSCAR_DEFAULT_CURRENCY = 'GBP'

# Max number of products to keep on the user's history
OSCAR_RECENTLY_VIEWED_PRODUCTS = 4

# Image paths
OSCAR_IMAGE_FOLDER = 'images/products/%Y/%m/'
OSCAR_PROMOTION_FOLDER = 'images/promotions/'

# Search settings
OSCAR_SEARCH_SUGGEST_LIMIT = 10

# Checkout
OSCAR_ALLOW_ANON_CHECKOUT = False

# Partners
OSCAR_PARTNER_WRAPPERS = {}

# Promotions
COUNTDOWN, LIST, SINGLE_PRODUCT, TABBED_BLOCK = ('Countdown', 'List', 'SingleProduct', 'TabbedBlock')
OSCAR_PROMOTION_MERCHANDISING_BLOCK_TYPES = (
    (COUNTDOWN, "Vertical list"),
    (LIST, "Horizontal list"),
    (TABBED_BLOCK, "Tabbed block"),
    (SINGLE_PRODUCT, "Single product"),
)

# Reviews
OSCAR_ALLOW_ANON_REVIEWS = True
OSCAR_MODERATE_REVIEWS = False

# Registration
OSCAR_SEND_REGISTRATION_EMAIL = True
OSCAR_FROM_EMAIL = 'oscar@example.com'

# Offers
OSCAR_OFFER_BLACKLIST_PRODUCT = None

# Max total number of items in basket
OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = None