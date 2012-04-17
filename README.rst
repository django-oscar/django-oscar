============================================
Django-Oscar - Flexible e-commerce on Django
============================================

*django-oscar* is an e-commerce framework for Django designed for building
domain-driven e-commerce sites.  It is structured such that any part of the
core functionality can be customised to suit the needs of your project.  This
allows it to handle a wide range of e-commerce requirements, from large-scale B2C
sites to complex B2B sites rich in domain-specific business logic.

This README is just a stub - see the following links for more details
information:

* `Official homepage`_ 
* `Documentation`_ on `readthedocs.org`_
* `Continuous integration homepage`_ on `travis-ci.org`_
* `Twitter account for news and updates`_
* `Twitter account of all commits`_

.. image:: https://secure.travis-ci.org/tangentlabs/django-oscar.png

.. _`Official homepage`: http://tangentlabs.github.com/django-oscar/
.. _`Documentation`: http://django-oscar.readthedocs.org/en/latest/
.. _`readthedocs.org`: http://readthedocs.org
.. _`Continuous integration homepage`: http://travis-ci.org/#!/tangentlabs/django-oscar 
.. _`travis-ci.org`: http://travis-ci.org/
.. _`Twitter account for news and updates`: https://twitter.com/#!/django_oscar
.. _`Twitter account of all commits`: https://twitter.com/#!/oscar_django

Oscar was written by David Winterbottom (`@codeinthehole`_) and is developed
and maintained by `Tangent Labs`_, a London-based digital agency.

.. _`@codeinthehole`: https://twitter.com/codeinthehole
.. _`Tangent Labs`: http://www.tangentlabs.co.uk

.. raw:: html

    <a href="https://twitter.com/share" class="twitter-share-button"
    data-url="https://github.com/tangentlabs/django-oscar"
    data-via="codeinthehole" data-size="large">Tweet</a>
    <script>!function(d,s,id){var
    js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src="//platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>

    <a href="https://twitter.com/django_oscar" class="twitter-follow-button"
    data-show-count="false" data-size="large">Follow @django_oscar</a>
    <script>!function(d,s,id){var
    js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src="//platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>

Changelog
---------

0.1
~~~

* Initial release - used in production by two major applications at Tangent
* Still a bit rough around the edges - docs aren't really good enough for
  non-Tangent people
* Docs are a bit stale and need updating in 0.2

Roadmap
-------

0.2
~~~

Currently a work-in-progress, estimated release date: April 2012.  It will feature:

* Much better documentation, including recipes for common tasks
* Refactoring of shipping methods
* New dashboard functionality for product management, order management, customer services
* New dynamic class loading
* Lots more tests!
* A fully styled sandbox shop based on Twitter's bootstrap.
