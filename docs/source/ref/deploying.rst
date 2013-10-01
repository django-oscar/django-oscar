===============
Deploying Oscar
===============

Oscar is a just a set of Django apps - it doesn't have any special deployment
requirements.  This page lists a couple of common things to be aware of when
deploying your Oscar site.

Performance
-----------

Oscar's templates are split into many partials and so it is recommended to use
the `cached template loader`_.

Sorl requires a cache backend to perform efficiently so ensure your ``CACHES``
setting points to a real key-value cache (like memcache).

Security
--------

Oscar relies on the Django framework for security measures and therefore no
Oscar specific configurations with regard to security are in place. See 
`Django's guidelines for security`_ for more information.

.. _`Django's guidelines for security`: _https://docs.djangoproject.com/en/dev/topics/security/
.. _`cached template loader`: https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
