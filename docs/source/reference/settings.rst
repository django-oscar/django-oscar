=======================
Oscar specific settings
=======================

Oscar provides a number of configurable settings used to confugre the system.

.. contents::
    :local:
    :depth: 1

Available settings
==================

OSCAR_SHOP_NAME
---------------

Default: ``Oscar``

The name of your e-commerce shop site.

OSCAR_SHOP_TAGLINE
------------------

Default: ``Domain-driven e-Commerce for Django``

The tagline that is displayed next to the shop name and in the browser title

OSCAR_ORDER_STATUS_PIPELINE
---------------------------

The pipeline defines the statuses that an order or line item can have and what
transitions are allowed in any given status. The pipeline is defined as a
dictionary where the keys are the available statuses. Allowed transitions are
defined as iterable values for the corresponding status. A sample pipeline
(as used in the Oscar sandbox) might look like this::

    OSCAR_INITIAL_ORDER_STATUS = 'Pending'
    OSCAR_INITIAL_LINE_STATUS = 'Pending'
    OSCAR_ORDER_STATUS_PIPELINE = {
        'Pending': ('Being processed', 'Cancelled',),
        'Being processed': ('Processed', 'Cancelled',),
        'Cancelled': (),
    }

OSCAR_INITIAL_ORDER_STATUS
--------------------------

The initial status used when a new order is submitted. This has to be a status
that is defined in the ``OSCAR_ORDER_STATUS_PIPELINE``.

OSCAR_INITIAL_LINE_STATUS
-------------------------

The status assigned to a line item when it is created as part of an new order. It
has to be a status defined in ``OSCAR_ORDER_STATUS_PIPELINE``.

OSCAR_ALLOW_ANON_CHECKOUT
-------------------------

Default: ``False``

Specifies if an anonymous user can buy products without creating an account.
If set to ``False`` a registered user is required to check out.

OSCAR_PARTNER_WRAPPERS
----------------------

Default: ``{}``

OSCAR_PROMOTION_MERCHANDISING_BLOCK_TYPES
-----------------------------------------

Default::

    COUNTDOWN, LIST, SINGLE_PRODUCT, TABBED_BLOCK = (
        'Countdown', 'List', 'SingleProduct', 'TabbedBlock')
    OSCAR_PROMOTION_MERCHANDISING_BLOCK_TYPES = (
        (COUNTDOWN, "Vertical list"),
        (LIST, "Horizontal list"),
        (TABBED_BLOCK, "Tabbed block"),
        (SINGLE_PRODUCT, "Single product"),
    )

Defines the available promotion block types that can be used in Oscar.

OSCAR_ALLOW_ANON_REVIEWS
------------------------

Default: ``True``

This setting defines whether an anonymous user can create a review for
a product without registering first. If it is set to ``True`` anonymous
users can create product reviews.

OSCAR_MODERATE_REVIEWS
----------------------

Default: ``False``

This defines whether reviews have to be moderated before they are publicly
available. If set to ``False`` a review created by a customer is immediately
visible on the product page.

OSCAR_EAGER_ALERTS
------------------

Default: ``True``

This enables sending alert notifications/emails instantly when products get
back in stock by listening to stock record update signals this might impact
performance for large numbers stock record updates.
Alternatively, the management command ``oscar_send_alerts`` can be used to
run periodically, e.g. as a cronjob. In this case instant alerts should be
disabled.

OSCAR_SEND_REGISTRATION_EMAIL
-----------------------------

Default: ``True``

Sending out *welcome* messages to a user after they have registered on the
site can be enabled or disabled using this setting. Setting it to ``True``
will send out emails on registration.

OSCAR_FROM_EMAIL
----------------

Default: ``oscar@example.com``

The email address used as the sender for all communication events and emails
handled by Oscar.

OSCAR_OFFER_BLACKLIST_PRODUCT
-----------------------------

Default: ``None``

OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
-----------------------------------

Default: ``None``

OSCAR_BASKET_COOKIE_OPEN
------------------------

Default: ``oscar_open_basket``

OSCAR_BASKET_COOKIE_SAVED
-------------------------

Default: ``oscar_saved_basket``

OSCAR_COOKIES_DELETE_ON_LOGOUT
------------------------------

Default: ``['oscar_recently_viewed_products', ]``

OSCAR_DEFAULT_CURRENCY
----------------------

Default: ``GBP``

This should be the symbol of the currency you wish Oscar to use by default.
This will be used by the currency templatetag.

OSCAR_CURRENCY_LOCALE
---------------------

Default: ``None``

This can be used to customise currency formatting. The value will be passed to
the ``format_currency`` function from the `Babel library`_.

.. _`Babel library`: http://babel.edgewall.org/wiki/ApiDocs/0.9/babel.numbers#babel.numbers:format_decimal

OSCAR_CURRENCY_FORMAT
---------------------

Default: ``None``

This can be used to customise currency formatting. The value will be passed to
the ``format_currency`` function from the Babel library.

OSCAR_BASKET_COOKIE_LIFETIME
----------------------------

Default: 604800 (1 week in seconds)

The time to live for the basket cookie in seconds

OSCAR_IMAGE_FOLDER
------------------

Default: ``images/products/%Y/%m/``

The path for uploading images to.

OSCAR_RECENTLY_VIEWED_PRODUCTS
------------------------------

Default: 20

The number of recently viewed products to store

OSCAR_SEARCH_SUGGEST_LIMIT
--------------------------

Default: 10

The number of suggestions that the search 'suggest' function should return
at maximum

OSCAR_IMAGE_FOLDER
------------------

Default: ``images/products/%Y/%m/``

The location within the ``MEDIA_ROOT`` folder that is used to store product images.
The folder name can contain date format strings as described in the `Django Docs`_.

.. _`Django Docs`: https://docs.djangoproject.com/en/dev/ref/models/fields/#filefield

OSCAR_PROMOTION_FOLDER
----------------------

Default: ``images/promotions/``

The folder within ``MEDIA_ROOT`` used for uploaded promotion images.

OSCAR_MISSING_IMAGE_URL
-----------------------

Default: ``image_not_found.jpg``

Copy this image from ``oscar/static/img`` to your ``MEDIA_ROOT`` folder. It needs to
be there so Sorl can resize it.

OSCAR_UPLOAD_ROOT
-----------------

Default: ``/tmp``

Deprecated settings
===================

There are currently no deprecated settings in Oscar.
