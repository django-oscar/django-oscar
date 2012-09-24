=======================
Oscar specific settings
=======================

Oscar provides a number of configurable settings used to confugre the system.

.. contents::
    :local:
    :depth: 1

Available settings
==================

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

Default: 4

The number of recently viewed products to store

OSCAR_SEARCH_SUGGEST_LIMIT
--------------------------

Default: 10

The number of suggestions that the search 'suggest' function should return
at maximum

Deprecated settings
===================

There are currently no deprecated settings in oscar
