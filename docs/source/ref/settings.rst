==============
Oscar settings
==============

This is a comprehensive list of all the settings Oscar provides.  All settings
are optional.

Display settings
================

``OSCAR_SHOP_NAME``
-------------------

Default: ``'Oscar'``

The name of your e-commerce shop site.  This is shown as the main logo within
the default templates.

``OSCAR_SHOP_TAGLINE``
----------------------

Default: ``''``

The tagline that is displayed next to the shop name and in the browser title.

``OSCAR_HOMEPAGE``
------------------

Default: ``reverse_lazy('catalogue:index')``

URL of home page of your site. This value is used for `Home` link in
navigation and redirection page after logout. Useful if you use a different app
to serve your homepage.

``OSCAR_ACCOUNTS_REDIRECT_URL``
-------------------------------

Default: ``'customer:profile-view'``

Oscar has a view that gets called any time the user clicks on 'My account' or
similar. By default it's a dumb redirect to the view configured with this
setting. But you could also override the view to display a more useful
account summary page or such like.

``OSCAR_RECENTLY_VIEWED_PRODUCTS``
----------------------------------

Default: 20

The number of recently viewed products to store.

``OSCAR_RECENTLY_VIEWED_COOKIE_LIFETIME``
-----------------------------------------

Default: 604800 (1 week in seconds)

The time to live for the cookie in seconds.

``OSCAR_RECENTLY_VIEWED_COOKIE_NAME``
-------------------------------------

Default: ``'oscar_history'``

The name of the cookie for showing recently viewed products.

``OSCAR_HIDDEN_FEATURES``
-------------------------

Defaults: ``[]``

Allows to disable particular Oscar feature in application and templates.
More information in the :doc:`/howto/how_to_disable_an_app_or_feature` document.

Pagination
----------

There are a number of settings that control pagination in Oscar's views. They
all default to 20.

- ``OSCAR_PRODUCTS_PER_PAGE``
- ``OSCAR_OFFERS_PER_PAGE``
- ``OSCAR_REVIEWS_PER_PAGE``
- ``OSCAR_NOTIFICATIONS_PER_PAGE``
- ``OSCAR_EMAILS_PER_PAGE``
- ``OSCAR_ORDERS_PER_PAGE``
- ``OSCAR_ADDRESSES_PER_PAGE``
- ``OSCAR_STOCK_ALERTS_PER_PAGE``
- ``OSCAR_DASHBOARD_ITEMS_PER_PAGE``

.. _oscar_search_facets:

``OSCAR_SEARCH_FACETS``
-----------------------

A dictionary that specifies the facets to use with the search backend.  It
needs to be a dict with keys ``fields`` and ``queries`` for field- and
query-type facets. Field-type facets can get an 'options' element with parameters like facet
sorting, filtering, etc.
The default is::

    OSCAR_SEARCH_FACETS = {
        'fields': {
            'product_class': {'name': _('Type'), 'field': 'product_class'},
            'rating': {'name': _('Rating'), 'field': 'rating'},
        },
        'queries': {
            'price_range': {
                 'name': _('Price range'),
                 'field': 'price',
                 'queries': [
                     # This is a list of (name, query) tuples where the name will
                     # be displayed on the front-end.
                     (_('0 to 20'), '[0 TO 20]'),
                     (_('20 to 40'), '[20 TO 40]'),
                     (_('40 to 60'), '[40 TO 60]'),
                     (_('60+'), '[60 TO *]'),
                 ]
             },
        },
    }

``OSCAR_PRODUCT_SEARCH_HANDLER``
--------------------------------

The search handler to be used in the product list views. If ``None``,
Oscar tries to guess the correct handler based on your Haystack settings.

Default::  ``None``

.. _OSCAR_DASHBOARD_NAVIGATION:

``OSCAR_DASHBOARD_NAVIGATION``
------------------------------

Default: see ``oscar.defaults`` (too long to include here).

A list of dashboard navigation elements. Usage is explained in
:doc:`/howto/how_to_configure_the_dashboard_navigation`.

``OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION``
-------------------------------------------

Default: ``'oscar.apps.dashboard.nav.default_access_fn'``

``OSCAR_DASHBOARD_NAVIGATION`` allows passing an access function for each node
which is used to determine whether to show the node for a specific user or not.
If no access function is defined, the function specified here is used.
The default function integrates with the permission-based dashboard and shows
the node if the user will be able to access it. That should be sufficient for
most cases.

Order settings
==============

``OSCAR_INITIAL_ORDER_STATUS``
------------------------------

The initial status used when a new order is submitted. This has to be a status
that is defined in the ``OSCAR_ORDER_STATUS_PIPELINE``.

``OSCAR_INITIAL_LINE_STATUS``
-----------------------------

The status assigned to a line item when it is created as part of an new order. It
has to be a status defined in ``OSCAR_LINE_STATUS_PIPELINE``.

``OSCAR_ORDER_STATUS_PIPELINE``
-------------------------------

Default: ``{}``

The pipeline defines the statuses that an order or line item can have and what
transitions are allowed in any given status. The pipeline is defined as a
dictionary where the keys are the available statuses. Allowed transitions are
defined as iterable values for the corresponding status.

A sample pipeline (as used in the Oscar sandbox) might look like this::

    OSCAR_INITIAL_ORDER_STATUS = 'Pending'
    OSCAR_INITIAL_LINE_STATUS = 'Pending'
    OSCAR_ORDER_STATUS_PIPELINE = {
        'Pending': ('Being processed', 'Cancelled',),
        'Being processed': ('Processed', 'Cancelled',),
        'Cancelled': (),
    }

``OSCAR_ORDER_STATUS_CASCADE``
------------------------------

This defines a mapping of status changes for order lines which 'cascade' down
from an order status change.

For example::

    OSCAR_ORDER_STATUS_CASCADE = {
        'Being processed': 'In progress'
    }

With this mapping, when an order has it's status set to 'Being processed', all
lines within it have their status set to 'In progress'.  In a sense, the status
change cascades down to the related objects.

Note that this cascade ignores restrictions from the
``OSCAR_LINE_STATUS_PIPELINE``.

``OSCAR_LINE_STATUS_PIPELINE``
------------------------------

Default: ``{}``

Same as ``OSCAR_ORDER_STATUS_PIPELINE`` but for lines.

Checkout settings
=================

``OSCAR_ALLOW_ANON_CHECKOUT``
-----------------------------

Default: ``False``

Specifies if an anonymous user can buy products without creating an account
first.  If set to ``False`` users are required to authenticate before they can
checkout (using Oscar's default checkout views).

``OSCAR_REQUIRED_ADDRESS_FIELDS``
---------------------------------

Default: ``('first_name', 'last_name', 'line1', 'line4', 'postcode', 'country')``

List of form fields that a user has to fill out to validate an address field.

Review settings
===============

``OSCAR_ALLOW_ANON_REVIEWS``
----------------------------

Default: ``True``

This setting defines whether an anonymous user can create a review for
a product without registering first. If it is set to ``True`` anonymous
users can create product reviews.

``OSCAR_MODERATE_REVIEWS``
--------------------------

Default: ``False``

This defines whether reviews have to be moderated before they are publicly
available. If set to ``False`` a review created by a customer is immediately
visible on the product page.

Communication settings
======================

``OSCAR_EAGER_ALERTS``
----------------------

Default: ``True``

This enables sending alert notifications/emails instantly when products get
back in stock by listening to stock record update signals this might impact
performance for large numbers stock record updates.
Alternatively, the management command ``oscar_send_alerts`` can be used to
run periodically, e.g. as a cronjob. In this case instant alerts should be
disabled.

``OSCAR_SEND_REGISTRATION_EMAIL``
---------------------------------

Default: ``True``

Sending out *welcome* messages to a user after they have registered on the
site can be enabled or disabled using this setting. Setting it to ``True``
will send out emails on registration.

``OSCAR_FROM_EMAIL``
--------------------

Default: ``oscar@example.com``

The email address used as the sender for all communication events and emails
handled by Oscar.

``OSCAR_STATIC_BASE_URL``
-------------------------

Default: ``None``

A URL which is passed into the templates for communication events.  It is not
used in Oscar's default templates but could be used to include static assets
(e.g. images) in a HTML email template.

``OSCAR_SAVE_SENT_EMAILS_TO_DB``
--------------------------------

Default: ``True``

Indicates if sent emails will be saved to database as instances of
``oscar.apps.communication.models.Email``.

Offer settings
==============

``OSCAR_OFFER_ROUNDING_FUNCTION``
---------------------------------

Default: Round down to the nearest hundredth of a unit using ``decimal.Decimal.quantize``

A dotted path to a function responsible for rounding decimal amounts
when offer discount calculations don't lead to legitimate currency values.

``OSCAR_OFFERS_INCL_TAX``
-------------------------

Default: ``False``

If ``True``, offers will be applied to prices including taxes instead of on
prices excluding tax. Oscar used to always calculate offers on prices excluding
tax so the default is ``False``. This setting also affects the meaning of
absolute prices in offers. So a flat discount of 10 pounds in an offer will
be treated as 10 pounds before taxes if ``OSCAR_OFFERS_INCL_TAX`` remains
``False`` and 10 pounds after taxes if ``OSCAR_OFFERS_INCL_TAX`` is set to
``True``.

``OSCAR_OFFERS_IMPLEMENTED_TYPES``
----------------------------------

Default::

    [
        'SITE',
        'VOUCHER',
    ]

A list of values from among those in the ``offer.ConditionalOffer.TYPE_CHOICES``
model attribute. The names of the model constants are used, instead of the
values themselves. This setting is used to restrict the selectable offer types
in the dashboard offers forms (``MetaDataForm`` and ``OfferSearchForm``), to
ones that Oscar currently implements.

Basket settings
===============

``OSCAR_BASKET_COOKIE_LIFETIME``
--------------------------------

Default: 604800 (1 week in seconds)

The time to live for the basket cookie in seconds.

``OSCAR_MAX_BASKET_QUANTITY_THRESHOLD``
---------------------------------------

Default: ``10000``

The maximum number of products that can be added to a basket at once. Set to
``None`` to disable the basket threshold limitation.


``OSCAR_BASKET_COOKIE_OPEN``
----------------------------

Default: ``'oscar_open_basket'``

The name of the cookie for the open basket.

Currency settings
=================

``OSCAR_DEFAULT_CURRENCY``
--------------------------

Default: ``GBP``

This should be the symbol of the currency you wish Oscar to use by default.
This will be used by the currency templatetag.

.. _currency-format-setting:

``OSCAR_CURRENCY_FORMAT``
-------------------------

Default: ``None``

Dictionary with arguments for the ``format_currency`` function from the `Babel library`_.
Contains next options: `format`, `format_type`, `currency_digits`.
For example::

    OSCAR_CURRENCY_FORMAT = {
        'USD': {
            'currency_digits': False,
            'format_type': "accounting",
        },
        'EUR': {
            'format': '#,##0\xa0¤',
        }
    }

.. _`Babel library`: http://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_currency

Upload/media settings
=====================

``OSCAR_IMAGE_FOLDER``
----------------------

Default: ``images/products/%Y/%m/``

The location within the ``MEDIA_ROOT`` folder that is used to store product images.
The folder name can contain date format strings as described in the `Django Docs`_.

.. _`Django Docs`: https://docs.djangoproject.com/en/stable/ref/models/fields/#filefield

``OSCAR_DELETE_IMAGE_FILES``
----------------------------

Default: ``True``

If enabled, a ``post_delete`` hook will attempt to delete any image files and
created thumbnails when a model with an ``ImageField`` is deleted. This is
usually desired, but might not be what you want when using a remote storage.

.. _missing-image-label:

``OSCAR_MISSING_IMAGE_URL``
---------------------------

Default: ``image_not_found.jpg``

Copy this image from ``oscar/static/img`` to your ``MEDIA_ROOT`` folder. It needs to
be there so the thumbnailer can resize it.


``OSCAR_THUMBNAILER``
---------------------

Default: ``'oscar.core.thumbnails.SorlThumbnail'``

Thumbnailer class that will be used to generate thumbnails. Available options:
``SorlThumbnail`` and ``EasyThumbnails``. To use them ``sorl-thumbnail`` or
``easy-thumbnails`` must be installed manually or with ``pip install django-oscar[sorl-thumbnail]`` or
``pip install django-oscar[easy-thumbnails]``. Custom thumbnailer class (based on
``oscar.core.thumbnails.AbstractThumbnailer``) can be used as well.

``OSCAR_THUMBNAIL_DEBUG``
-------------------------

Default: Same as ``DEBUG``

When set to ``True`` the ``ThumbnailNode.render`` method can raise errors. Django recommends that tags never raise errors in the ``Node.render`` method in production.

Slug settings
=============

``OSCAR_SLUG_FUNCTION``
-----------------------

Default: ``'oscar.core.utils.default_slugifier'``

A dotted path to the :py:func:`slugify <oscar.core.utils.default_slugifier>` function to use.

Example::

    # in myproject.utils
    def some_slugify(value, allow_unicode=False):
        return value

    # in settings.py
    OSCAR_SLUG_FUNCTION = 'myproject.utils.some_slugify'

``OSCAR_SLUG_MAP``
------------------

Default: ``{}``

A dictionary to target:replacement strings that the :py:func:`slugify <oscar.core.utils.default_slugifier>` function will
apply before slugifying the value. This is useful when names contain
characters which would normally be stripped. For instance::

    OSCAR_SLUG_MAP = {
        'c++': 'cpp',
        'f#': 'fsharp',
    }

``OSCAR_SLUG_BLACKLIST``
------------------------

Default: ``[]``

An iterable of words the :py:func:`slugify <oscar.core.utils.default_slugifier>` function will try to remove after the value
has been slugified. Note, a word will not be removed from the slug if it would
result in an empty slug.

Example::

    # With OSCAR_SLUG_BLACKLIST = ['the']
    slugify('The cat')
    > 'cat'

    # With OSCAR_SLUG_BLACKLIST = ['the', 'cat']
    slugify('The cat')
    > 'cat'

``OSCAR_SLUG_ALLOW_UNICODE``
----------------------------

Default: ``False``

Allows Unicode characters in slugs generated by ``AutoSlugField``,
which is supported by the underlying ``SlugField`` in Django>=1.9.


Dynamic importer settings
=========================

``OSCAR_DYNAMIC_CLASS_LOADER``
----------------------------------

Default: ``oscar.core.loading.default_class_loader``

A dotted path to the callable used to dynamically import classes.


Misc settings
=============

``OSCAR_COOKIES_DELETE_ON_LOGOUT``
----------------------------------

Default: ``['oscar_recently_viewed_products',]``

Which cookies to delete automatically when the user logs out.

``OSCAR_GOOGLE_ANALYTICS_ID``
-----------------------------

Tracking ID for Google Analytics tracking code, available as `google_analytics_id` in the template
context. If setting is set, enables Universal Analytics tracking code for page views and
transactions.


``OSCAR_CSV_INCLUDE_BOM``
-------------------------

Default: ``False``

A flag to control whether Oscar's CSV writer should prepend a byte order mark
(BOM) to CSV files that are encoded in UTF-8. Useful for compatibility with some
CSV readers, Microsoft Excel in particular.


``OSCAR_URL_SCHEMA``
--------------------

Default: ``http``

The schema that will be used to build absolute url in ``absolute_url`` template tag.
