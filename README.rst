.. image:: http://img692.imageshack.us/img692/6498/logovf.png

===================================
Domain-driven e-commerce for Django
===================================

Oscar is an e-commerce framework for Django designed for building domain-driven
sites.  It is structured such that any part of the core functionality can be
customised to suit the needs of your project.  This allows a wide range of
e-commerce requirements to be handled, from large-scale B2C sites to complex B2B
sites rich in domain-specific business logic.

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/oscarcommerce.thumb.png
    :target: http://oscarcommerce.com

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/readthedocs.thumb.png
    :target: http://django-oscar.readthedocs.org/en/latest/

Further reading:

* `Official homepage`_
* `Sandbox site`_ (an hourly build of the unstable master branch - it's
  experimental but feel free to explore and get a feel for the base Oscar
  install.  Polished demo site coming soon)
* `Documentation`_ on the excellent `readthedocs.org`_
* `Google Group`_ - the mailing list is django-oscar@googlegroups.com
* `Continuous integration homepage`_ on `travis-ci.org`_
* `Twitter account for news and updates`_
* `Twitter account of all commits`_
* `crate.io page`_
* `PyPI page`_
* `Transifex project`_ - translating Oscar made easy

Continuous integration status:

.. image:: https://secure.travis-ci.org/tangentlabs/django-oscar.png
    :target: http://travis-ci.org/#!/tangentlabs/django-oscar

.. _`Official homepage`: http://oscarcommerce.com
.. _`Sandbox site`: http://latest.oscarcommerce.com
.. _`Documentation`: http://django-oscar.readthedocs.org/en/latest/
.. _`readthedocs.org`: http://readthedocs.org
.. _`Continuous integration homepage`: http://travis-ci.org/#!/tangentlabs/django-oscar
.. _`travis-ci.org`: http://travis-ci.org/
.. _`Twitter account for news and updates`: https://twitter.com/#!/django_oscar
.. _`Twitter account of all commits`: https://twitter.com/#!/oscar_django
.. _`Google Group`: https://groups.google.com/forum/?fromgroups#!forum/django-oscar
.. _`crate.io page`: https://crate.io/packages/django-oscar/
.. _`PyPI page`: http://pypi.python.org/pypi/django-oscar/
.. _`Transifex project`: https://www.transifex.com/projects/p/django-oscar/

Oscar was written by `David Winterbottom`_ (`@codeinthehole`_) and is developed
and maintained by `Tangent Labs`_, a London-based digital agency, with help from
`Mirumee`_.

.. _`Mirumee`: http://mirumee.com/

.. _`David Winterbottom`: http://codeinthehole.com
.. _`@codeinthehole`: https://twitter.com/codeinthehole
.. _`Tangent Labs`: http://www.tangentlabs.co.uk
.. _`Mirumee`: http://mirumee.com/

Screenshots
-----------

These are a few screenshots from the 'sandbox' example site that ships with
Oscar.  It sports a simple design built with Twitter's Bootstrap_.  It provides a
good starting point for quickly building elegant e-commerce sites.

.. _Bootstrap: http://twitter.github.com/bootstrap/

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/browse.thumb.png
    :target: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/browse.png

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/detail.thumb.png
    :target: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/detail.png

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/basket.thumb.png
    :target: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/basket.png

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/dashboard.thumb.png
    :target: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/dashboard.png

You can have this sample shop running on your machine in 5 commands::

    $ git clone git@github.com:tangentlabs/django-oscar.git
    $ cd django-oscar
    $ mkvirtualenv oscar
    $ make sandbox
    $ sites/sandbox/manage.py runserver

The sandbox site (initialised with a sample set of products) will be available
at: http://localhost:8000.  A sample superuser is installed with credentials::

    username: superuser
    email: superuser@example.com
    password: testing

Want to make changes?  Check out the `contributing guidelines`_.

.. _`contributing guidelines`: http://django-oscar.readthedocs.org/en/latest/contributing.html#playing-in-the-sandbox

The sandbox site is also available to browse at
http://latest.oscarcommerce.com

Translations can be contributed using Transifex_.

.. _Transifex: https://www.transifex.com/projects/p/django-oscar/

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
* django-oscar-testsupport_ - Testing utilities for Oscar extensions.

.. _django-oscar-datacash: https://github.com/tangentlabs/django-oscar-datacash
.. _django-oscar-paymentexpress: https://github.com/tangentlabs/django-oscar-paymentexpress
.. _`Payment Express`: http://www.paymentexpress.com
.. _DataCash: http://www.datacash.com/
.. _django-oscar-paypal: https://github.com/tangentlabs/django-oscar-paypal
.. _`Express Checkout`: https://www.paypal.com/uk/cgi-bin/webscr?cmd=_additional-payment-ref-impl1
.. _`PayFlow Pro`: https://merchant.paypal.com/us/cgi-bin/?cmd=_render-content&content_ID=merchant/payment_gateway
.. _django-oscar-gocardless: https://github.com/tangentlabs/django-oscar-gocardless
.. _GoCardless: https://gocardless.com/
.. _django-oscar-jirafe: https://github.com/tangentlabs/django-oscar-jirafe
.. _Jirafe: https://jirafe.com/
.. _django-oscar-accounts: https://github.com/tangentlabs/django-oscar-accounts
.. _django-oscar-testsupport: https://github.com/tangentlabs/django-oscar-testsupport

The following extensions are in development:

* django-oscar-gocardless_ - Integration with the GoCardless_ payment gateway
* django-oscar-jirafe_ - Integration with the Jirafe_ analytics package
* django-oscar-parachute_ - Import scripts for migrating away from non-Oscar
  platforms.
* django-oscar-approval_ - Approval workflow for authorising new
  orders/products.

.. _django-oscar-stores: https://github.com/tangentlabs/django-oscar-stores
.. _django-oscar-parachute: https://github.com/tangentlabs/django-oscar-parachute
.. _django-oscar-approval: https://github.com/tangentlabs/django-oscar-approval

Let us know if you're writing a new one!

License
-------

Oscar is released under the permissive `New BSD license`_.

.. _`New BSD license`: https://github.com/tangentlabs/django-oscar/blob/master/LICENSE

Case studies
------------

Oscar is still in active development, but is used in production by a range of
companies, from large multinationals to small, boutique stores:

Tangent projects:

* Tata Group - http://www.landmarkonthenet.com
* Carlsberg - Their global "We Deliver More" platform is powered by Oscar (but
  is a B2B site and not browsable by the public)
* Chocolate Box - https://www.thechocolatebox.com.au
* The UK Labour party - http://shop.labour.org.uk
* Meridian Audio - http://www.meridian-audio.co.uk

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/landmark.thumb.png
    :target: http://www.landmarkonthenet.com

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/carlsberg.cch.thumb.png
    :target: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/carlsberg.cch.png

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/chocolatebox.thumb.png
    :target: https://www.thechocolatebox.com.au

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/labourshop.thumb.png
    :target: https://shop.labour.org.uk

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/meridian.thumb.png
    :target: http://www.meridian-audio.co.uk

Non-Tangent:

* Dolbeau - http://www.dolbeau.ca/
* Sobusa - http://www.sobusa.fr/
* Laivee - http://laivee.pl
* Colinss - http://colinss.com

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/dolbeau.thumb.png
    :target: http://www.dolbeau.ca

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/sobusa.thumb.png
    :target: http://www.sobusa.fr

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/laivee.thumb.png
    :target: http://www.laivee.pl

.. image:: https://github.com/tangentlabs/django-oscar/raw/master/docs/images/screenshots/colinss.thumb.png
    :target: http://www.colinss.com

Many more on the way.  If you use Oscar in production, please let us know.

Would you like to work on Oscar?
--------------------------------

Tangent Labs are currently looking for python hackers to work on Oscar as well
as some of other internal products and e-commerce projects.  If this sounds
interesting, please get in touch with @codeinthehole through Github or Twitter.
The position is in Tangent's London offices.
