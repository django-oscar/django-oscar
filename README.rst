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
    :target: https://django-oscar.readthedocs.io/en/latest/

Further reading:

* `Official homepage`_
* `Sandbox site`_ (an hourly build of the unstable master branch - it's
  experimental but feel free to explore and get a feel for the base Oscar
  install.)
* `Documentation`_ on the excellent `readthedocs.org`_
* `django-oscar group`_ - mailing list for questions and announcements
* `django-oscar-jobs group`_ - mailing list for job offers
* `Continuous integration homepage`_ on `travis-ci.org`_
* `Twitter account for news and updates`_
* #django-oscar on Freenode (community-run IRC channel) with `public logs`_
* `PyPI page`_
* `Transifex project`_ - translating Oscar made easy

Continuous integration status:

.. image:: https://travis-ci.org/django-oscar/django-oscar.svg?branch=master
    :target: https://travis-ci.org/django-oscar/django-oscar

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

.. _`Official homepage`: http://oscarcommerce.com
.. _`Sandbox site`: http://latest.oscarcommerce.com
.. _`Documentation`: https://django-oscar.readthedocs.io/en/latest/
.. _`readthedocs.org`: http://readthedocs.org
.. _`Continuous integration homepage`: http://travis-ci.org/#!/django-oscar/django-oscar
.. _`travis-ci.org`: http://travis-ci.org/
.. _`Twitter account for news and updates`: https://twitter.com/#!/django_oscar
.. _`public logs`: https://botbot.me/freenode/django-oscar/
.. _`django-oscar group`: https://groups.google.com/forum/?fromgroups#!forum/django-oscar
.. _`django-oscar-jobs group`: https://groups.google.com/forum/?fromgroups#!forum/django-oscar-jobs
.. _`PyPI page`: https://pypi.python.org/pypi/django-oscar/
.. _`Transifex project`: https://www.transifex.com/projects/p/django-oscar/

Core team:

- `David Winterbottom`_ (Twitter `@codeinthehole`_)
- `Maik Hoepfel`_ (Twitter `@maikhoepfel`_)
- `Markus Bertheau`_
- `Michael van Tellingen`_

.. _`David Winterbottom`: https://github.com/codeinthehole
.. _`@codeinthehole`: https://twitter.com/codeinthehole
.. _`Maik Hoepfel`: https://github.com/maikhoepfel
.. _`@maikhoepfel`: https://twitter.com/maikhoepfel
.. _`Markus Bertheau`: https://github.com/mbertheau
.. _`Michael van Tellingen`: https://github.com/mvantellingen

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

The sandbox site is also available to browse at
http://latest.oscarcommerce.com.  Dashboard users can be created using `this
gateway page`_.

The sandbox site can be set-up locally `in 5 commands`_.  Want to
make changes?  Check out the `contributing guidelines`_.

.. _`this gateway page`: http://latest.oscarcommerce.com/gateway/
.. _`in 5 commands`: https://django-oscar.readthedocs.io/en/latest/internals/sandbox.html#running-the-sandbox-locally
.. _`contributing guidelines`: https://django-oscar.readthedocs.io/en/latest/internals/contributing/index.html


Extensions
----------

The following extensions are stable and ready for use:

* django-oscar-datacash_ - Integration with the DataCash_ payment gateway

* django-oscar-paypal_ - Integration with PayPal.  This currently supports both
  `Express Checkout`_ and `PayFlow Pro`_.

* django-oscar-paymentexpress_ - Integration with the `Payment Express`_ payment
  gateway

* django-oscar-accounts_ - Managed accounts (can be used for giftcard
  functionality and loyalty schemes)

* django-oscar-stores_ - Physical stores integration (opening hours, store
  locator etc)

* django-oscar-eway_ - Integration with the eWay_ payment gateway.

* django-oscar-sagepay-direct_ - Integration with "DIRECT" part of Sagepay's API

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
.. _django-oscar-eway: https://github.com/snowball-one/django-oscar-eway
.. _django-oscar-stores: https://github.com/django-oscar/django-oscar-stores
.. _django-oscar-sagepay-direct: https://github.com/django-oscar/django-oscar-sagepay-direct
.. _eWay: https://www.eway.com.au

The following are community-written extensions:

* django-oscar-payments_ - Pluggable payments for Oscar
* django-oscar-recurly_ - Integration with the Recurly payment gateway
* django-oscar-adyen_ - Integration with the Adyen payment gateway
* django-oscar-przelewy24_ - Integration with the Przelewy24 payment gateway
* oscar-sagepay_ - Payment integration with Sage Pay
* django-oscar-erp_

Let us know if you're writing a new one!

.. _django-oscar-unicredit: https://bitbucket.org/marsim/django-oscar-unicredit/
.. _django-oscar-erp: https://bitbucket.org/zikzakmedia/django-oscar_erp
.. _django-oscar-payments: https://github.com/Lacrymology/django-oscar-payments
.. _django-oscar-recurly: https://github.com/mynameisgabe/django-oscar-recurly
.. _django-oscar-adyen: https://github.com/oscaro/django-oscar-adyen
.. _django-oscar-przelewy24: https://github.com/kisiel/django-oscar-przelewy24
.. _oscar-sagepay: https://github.com/udox/oscar-sagepay

License
-------

Oscar is released under the permissive `New BSD license`_ (see summary_).

.. _summary: https://tldrlegal.com/license/bsd-3-clause-license-(revised)

.. _`New BSD license`: https://github.com/django-oscar/django-oscar/blob/master/LICENSE

Case studies
------------

Oscar is still in active development but is used in production by a range of
companies, from large multinationals to small, boutique stores:

Selected Tangent projects:

* Tata Group - http://www.landmarkonthenet.com
* Carlsberg - Their global "We Deliver More" platform is powered by Oscar (but
  is a B2B site and not browsable by the public)
* Chocolate Box - https://www.chocolatebox.com.au
* The UK Labour party - http://shop.labour.org.uk
* Meridian Audio - http://www.meridian-audio.co.uk
* Which Rightchoice - http://www.whichrightchoice.com
* Freetix - http://www.freetix.com.au/
* Nails inc US - http://www.nailsinc.com/us/

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/landmark.thumb.png
    :target: http://www.landmarkonthenet.com

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/carlsberg.cch.thumb.png
    :target: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/carlsberg.cch.png

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/chocolatebox.thumb.png
    :target: https://www.chocolatebox.com.au

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/labourshop.thumb.png
    :target: https://shop.labour.org.uk

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/meridian.thumb.png
    :target: http://www.meridian-audio.co.uk

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/rightchoice.thumb.png
    :target: http://www.whichrightchoice.com

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/freetix.thumb.png
    :target: http://www.freetix.com.au/

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/nailsinc.thumb.png
    :target: http://www.nailsinc.com/us/

Non-Tangent:

* Dolbeau - http://www.dolbeau.ca
* Audio App - https://audioapp.pl
* Anything Gift - http://www.anythinggift.co.uk
* Partecipa Cards - http://www.partecipacards.com
* Chiyome - https://chiyome.com
* Bike Parts Market - https://www.bikepartsmarket.com

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/dolbeau.thumb.png
    :target: http://www.dolbeau.ca

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/audioapp.thumb.png
    :target: https://audioapp.pl

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/anythinggift.thumb.png
    :target: http://www.anythinggift.co.uk

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/partecipacards.thumb.png
    :target: http://www.partecipacards.com

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/chiyome.thumb.png
    :target: https://chiyome.com

.. image:: https://github.com/django-oscar/django-oscar/raw/master/docs/images/screenshots/bpm.thumb.png
    :target: https://www.bikepartsmarket.com

Many more on the way.  If you use Oscar in production, please let us know.

Looking for commercial support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are interested in having an Oscar project built for you, or for
development of an existing Oscar site, Tangent can
help.  Please get in touch via `oscar@tangentlabs.co.uk`_ or via the `Tangent
Snowball`_ site.

.. _`oscar@tangentlabs.co.uk`: mailto:oscar@tangentlabs.co.uk
.. _`Tangent Snowball`: http://www.tangentsnowball.com/products/oscar
