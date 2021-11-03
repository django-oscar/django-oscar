.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/logos/oscar.png
    :target: http://oscarcommerce.com

===================================
Domain-driven e-commerce for Django
===================================


Oscar is an e-commerce framework for Django designed for building domain-driven
sites.  It is structured such that any part of the core functionality can be
customised to suit the needs of your project.  This allows a wide range of
e-commerce requirements to be handled, from large-scale B2C sites to complex B2B
sites rich in domain-specific business logic.

Contents:

.. contents:: :local:

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/oscarcommerce.thumb.png
    :target: http://oscarcommerce.com

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/readthedocs.thumb.png
    :target: https://django-oscar.readthedocs.io/en/stable/

Further reading:

* `Official homepage`_
* `Sandbox site`_ (automatically deployed via the official docker sandbox image)
* `Documentation`_ on the excellent `readthedocs.org`_
* `Docker image`_ on http://hub.docker.com/
* `django-oscar group`_ - mailing list for questions and announcements
* `Twitter account for news and updates`_
* `Slack`_
* `PyPI page`_
* `Transifex project`_ - translating Oscar made easy

.. start-no-pypi

Continuous integration status:

.. image:: https://github.com/django-oscar/django-oscar/workflows/Tests/badge.svg

.. image:: http://codecov.io/github/django-oscar/django-oscar/coverage.svg?branch=master
    :alt: Coverage
    :target: http://codecov.io/github/django-oscar/django-oscar?branch=master

.. image:: https://requires.io/github/django-oscar/django-oscar/requirements.svg?branch=master
     :target: https://requires.io/github/django-oscar/django-oscar/requirements/?branch=master
     :alt: Requirements Status

PyPI status:

.. image:: https://img.shields.io/pypi/v/django-oscar.svg
    :target: https://pypi.python.org/pypi/django-oscar/

Docs status:

.. image:: https://readthedocs.org/projects/django-oscar/badge/
   :target: https://readthedocs.org/projects/django-oscar/
   :alt: Documentation Status

.. end-no-pypi

.. _`Official homepage`: http://oscarcommerce.com
.. _`Sandbox site`: https://latest.oscarcommerce.com
.. _`Docker image`: https://hub.docker.com/r/oscarcommerce/django-oscar-sandbox/
.. _`Documentation`: https://django-oscar.readthedocs.io/en/stable/
.. _`readthedocs.org`: http://readthedocs.org
.. _`Twitter account for news and updates`: https://twitter.com/#!/django_oscar
.. _`django-oscar group`: https://groups.google.com/forum/?fromgroups#!forum/django-oscar
.. _`PyPI page`: https://pypi.python.org/pypi/django-oscar/
.. _`Transifex project`: https://www.transifex.com/projects/p/django-oscar/
.. _`Slack`: https://slack.oscarcommerce.com/

Core team:

- `David Winterbottom`_ (Twitter `@codeinthehole`_)
- `Maik Hoepfel`_ (Twitter `@maikhoepfel`_)
- `Markus Bertheau`_
- `Michael van Tellingen`_
- `Alexander Gaevsky`_
- `Samir Shah`_

.. _`David Winterbottom`: https://github.com/codeinthehole
.. _`@codeinthehole`: https://twitter.com/codeinthehole
.. _`Maik Hoepfel`: https://github.com/maikhoepfel
.. _`@maikhoepfel`: https://twitter.com/maikhoepfel
.. _`Markus Bertheau`: https://github.com/mbertheau
.. _`Michael van Tellingen`: https://github.com/mvantellingen
.. _`Alexander Gaevsky`: https://github.com/sasha0
.. _`Samir Shah`: https://github.com/solarissmoke


Supported versions
------------------

The currently supported versions of Oscar are:

+---------+----------------+
| Version | End of support |
+=========+================+
| 3.1     | April 2022     |
+---------+----------------+
| 3.0     | May 2021       |
+---------+----------------+
| 2.2 LTS | August 2023    |
+---------+----------------+

Supported verions are eligible for fixes for data loss bugs and security issues. Releases designated as
Long-term support (LTS) releases will receive support for an extended period of 3 years from their release date.


Screenshots
-----------

Sandbox
~~~~~~~

These are screenshots from the 'sandbox' example site that ships with
Oscar.  It sports a simple design built with Twitter's Bootstrap_ and provides a
good starting point for rapidly building elegant e-commerce sites.

.. _Bootstrap: https://getbootstrap.com/

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/browse.thumb.png
    :target: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/browse.png

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/detail.thumb.png
    :target: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/detail.png

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/basket.thumb.png
    :target: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/basket.png

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/dashboard.thumb.png
    :target: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/dashboard.png

The sandbox site is also available to browse at https://latest.oscarcommerce.com.

The sandbox site can be set-up locally `in 5 commands`_.  Want to
make changes?  Check out the `contributing guidelines`_.

.. _`in 5 commands`: https://django-oscar.readthedocs.io/en/stable/internals/sandbox.html#running-the-sandbox-locally
.. _`contributing guidelines`: https://django-oscar.readthedocs.io/en/stable/internals/contributing/index.html


Extensions
----------

The following extensions are stable and ready for use:

* django-oscar-api_ - RESTful JSON API for django-oscar

* django-oscar-adyen_ - Integration with the Adyen payment gateway

* django-oscar-datacash_ - Integration with the DataCash_ payment gateway

* django-oscar-paypal_ - Integration with PayPal.  This currently supports both
  `Express Checkout`_ and `PayFlow Pro`_.

* django-oscar-paymentexpress_ - Integration with the `Payment Express`_ payment
  gateway

* django-oscar-accounts_ - Managed accounts (can be used for giftcard
  functionality and loyalty schemes)

* django-oscar-stores_ - Physical stores integration (opening hours, store
  locator etc)

* django-oscar-sagepay-direct_ - Integration with "DIRECT" part of Sagepay's API

* django_oscar_docdata_ - Integration with Docdata_ payment gateway.

* django_oscar_invoices_ - Invoices or receipts generation for the
  Oscar

.. _django-oscar-api: https://github.com/django-oscar/django-oscar-api
.. _django-oscar-adyen: https://github.com/django-oscar/django-oscar-adyen
.. _django-oscar-datacash: https://github.com/django-oscar/django-oscar-datacash
.. _django-oscar-paymentexpress: https://github.com/django-oscar/django-oscar-paymentexpress
.. _`Payment Express`: http://www.paymentexpress.com
.. _DataCash: http://www.datacash.com/
.. _django-oscar-paypal: https://github.com/django-oscar/django-oscar-paypal
.. _`Express Checkout`: https://www.paypal.com/uk/cgi-bin/webscr?cmd=_additional-payment-ref-impl1
.. _`PayFlow Pro`: https://merchant.paypal.com/us/cgi-bin/?cmd=_render-content&content_ID=merchant/payment_gateway
.. _django-oscar-accounts: https://github.com/django-oscar/django-oscar-accounts
.. _django-oscar-easyrec: https://github.com/django-oscar/django-oscar-easyrec
.. _EasyRec: http://easyrec.org/
.. _django-oscar-stores: https://github.com/django-oscar/django-oscar-stores
.. _django-oscar-sagepay-direct: https://github.com/django-oscar/django-oscar-sagepay-direct
.. _eWay: https://www.eway.com.au
.. _django_oscar_docdata: https://github.com/django-oscar/django-oscar-docdata
.. _Docdata: https://www.docdatapayments.com/
.. _django_oscar_invoices: https://github.com/django-oscar/django-oscar-invoices

The following are community-written extensions:

* django-oscar-payments_ - Pluggable payments for Oscar

* oscar-sagepay_ - Payment integration with Sage Pay

* django-oscar-support_ - Customer services and ticketing plugin for Oscar

* django-oscar-api-checkout_ - Oscar API Checkout is a layer on top of
  django-oscar and django-oscar-api, adding support for more complex and
  multiple payment options during an API checkout.

* django-oscar-bundles_ - Oscar Bundles adds multi-product bundles to
  django-oscar.

* django-oscar-bluelight_ - `Bluelight Specials`_ is a layer on-top of
  django-oscar that adds support for more complex offers and vouchers,
  including conjunctive and disjunctive compound conditions.

* django-oscar-cch_ - Oscar CCH is a plugin for django-oscar adding support
  for calculating taxes using the Wolters Kluwer `CCH Sales Tax Office`_ SOAP
  API.

* django-oscar-cybersource_ - Oscar CyberSource is a plugin for Oscar API
  Checkout that makes it possible to use
  `CyberSource Secure Acceptance Silent Order Post`_ as an order payment
  method.

* django-oscar-wfrs_ - Oscar WFRS is a plugin for django-oscar-api-checkout_
  that makes it possible to use `Wells Fargo Retail Services`_ as an order
  payment method.

Let us know if you're writing a new one!

.. _django-oscar-payments: https://github.com/Lacrymology/django-oscar-payments
.. _oscar-sagepay: https://github.com/udox/oscar-sagepay
.. _django-oscar-support: https://github.com/SalahAdDin/django-oscar-support
.. _django-oscar-api-checkout: https://github.com/thelabnyc/django-oscar-api-checkout
.. _django-oscar-bundles: https://github.com/thelabnyc/django-oscar-bundles
.. _django-oscar-bluelight: https://github.com/thelabnyc/django-oscar-bluelight
.. _`Bluelight Specials`: https://en.wiktionary.org/wiki/blue-light_special
.. _django-oscar-cch: https://github.com/thelabnyc/django-oscar-cch
.. _`CCH Sales Tax Office`: http://www.salestax.com/solutions/calculation/cch-salestax-office/
.. _django-oscar-cybersource: https://github.com/thelabnyc/django-oscar-cybersource
.. _`CyberSource Secure Acceptance Silent Order Post`: https://www.cybersource.com/products/payment_security/secure_acceptance_silent_order_post/
.. _django-oscar-wfrs: https://github.com/thelabnyc/django-oscar-wfrs
.. _`Wells Fargo Retail Services`: https://retailservices.wellsfargo.com/

Videos
------

Videos with talks about Oscar:

* `An introduction to Django-oscar`_ by `David Winterbottom`_, DjangoCon Europe 2014
* `Oscar and the art of transactional Django applications`_ by `David Winterbottom`_, PyCon PL 2014
* `The Tale of Oscar and the API`_ by `Kees Hink`_, PyGrunn 2017

.. _`An introduction to Django-oscar`: https://youtu.be/o4ol6EzGDSw
.. _`Oscar and the art of transactional Django applications`: https://youtu.be/datKUNTKYz8
.. _`The Tale of Oscar and the API`: https://youtu.be/YPnKoiyGIHM
.. _`Kees Hink`: https://github.com/khink

License
-------

Oscar is released under the permissive `New BSD license`_ (see summary_).

.. _summary: https://tldrlegal.com/license/bsd-3-clause-license-(revised)

.. _`New BSD license`: https://github.com/django-oscar/django-oscar/blob/master/LICENSE

Case studies
------------

Oscar is still in active development but is used in production by a range of
companies, from large multinationals to small, boutique stores. See
http://oscarcommerce.com/cases.html for an overview.

Many more on the way.  If you use Oscar in production, please `let us know`_.

.. _`let us know`: https://github.com/django-oscar/oscarcommerce.com/issues

Looking for commercial support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are interested in having an Oscar project built for you, or for
development of an existing Oscar site then please get in touch via `info@oscarcommerce.com`_.

.. _`info@oscarcommerce.com`: mailto:info@oscarcommerce.com
