===============
Deploying Oscar
===============

Oscar is a just a set of Django apps - it doesn't have any special deployment
requirements. That means the excellent Django docs for `deployment`_
should be your first stop. This page then only distills some of the experience
gained from running Oscar projects.

Performance
-----------

Setting up caching is crucial for a good performance. Oscar's templates are
split into many partials, hence it is recommended to use the
`cached template loader`_. Sorl also will hit your database hard if you run it
without a cache backend.

If your memory constraints are tight and you can only run one Python worker,
LocMemCache will usually outperform external cache backends due to the lower
overhead. But once you can scale beyond one worker, it might make good sense to
switch to something like memcached or redis.

Blocking in views should be avoided if possible. That is especially true for
external API calls and sending emails. Django's pluggable email backends allow
for switching out the blocking SMTP backend to a custom non-blocking solution.
Possible options are storing emails in a database or cache for later consumption
or triggering an external worker, e.g. via `django-celery`_.
`django_post-office`_ works nicely.

For backwards-compatibility reasons, Django doesn't enable database connection
pooling by default. Performance is likely to improve when enabled.

Security
--------

Oscar relies on the Django framework for security measures and therefore no
Oscar specific configurations with regard to security are in place. See 
`Django's guidelines for security`_ for more information.

`django-secure`_ is a nice app that comes with a few sanity checks for
deployments behind SSL.

Search Engine Optimisation
--------------------------

A basic example of what a sitemap for Oscar could look like has been added
to the sandbox site. Have a look at ``sandbox/urls.py`` for inspiration.

.. _deployment: https://docs.djangoproject.com/en/dev/howto/deployment/
.. _`Django's guidelines for security`: https://docs.djangoproject.com/en/dev/topics/security/
.. _`cached template loader`: https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
.. _django-celery: http://www.celeryproject.org/
.. _django-secure: https://pypi.python.org/pypi/django-secure
.. _django_post-office: https://github.com/ui/django-post_office
