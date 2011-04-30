DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'oscar',                      # Or path to database file if using sqlite3.
        'USER': 'oscar',                      # Not used with sqlite3.
        'PASSWORD': 'hellokitty',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Google checkout 
GOOGLE_CHECKOUT_MERCHANT_ID = '921791062562645'
GOOGLE_CHECKOUT_MERCHANT_KEY = 'ba3VMi0dFHqKKSDEfoAuLA'
GOOGLE_CHECKOUT_URL = 'https://sandbox.google.com/checkout/api/checkout/v2/merchantCheckout/Merchant/%s' % GOOGLE_CHECKOUT_MERCHANT_ID

# Datacash
DATACASH_URL = 'https://testserver.datacash.com/Transaction'         
DATACASH_USERNAME = '99002051'
DATACASH_PASSWORD = 'Ys4ePPgDHQmn'