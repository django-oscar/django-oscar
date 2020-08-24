==========================
How to customise templates
==========================

Assuming you want to use Oscar's templates in your project, there are two
options.  You don't have to though - you could write all your own templates if
you like.  If you do this, it's probably best to start with a straight copy of
all of Oscar's templates so you know all the files that you need to
re-implement.

Anyway - here are the two options for customising.

Method 1 - Forking
------------------

One option is always just to fork the template into your local project so that
it comes first in the include path.

Say you want to customise ``base.html``.  First you need a project-specific
templates directory that comes first in the include path.  You can set this up
as so::



    import os
    location = lambda x: os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', x)

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                location('templates'), # templates directory of the project
            ],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    ...
                    'oscar.core.context_processors.metadata',
                ],
            },
        },
    ]

Next copy Oscar's ``base.html`` into your templates directory and customise it
to suit your needs.

The downsides of this method are that it involves duplicating the file from
Oscar in a way that breaks the link with upstream.  Hence, changes to Oscar's
``base.html`` won't be picked up by your project as you will have your own
version.

Method 2 - Subclass parent but use same template path
-----------------------------------------------------

There is a trick you can perform whereby Oscar's templates can be accessed via
two paths.  This is outlined in the `Django wiki`_.

.. _`Django wiki`: https://code.djangoproject.com/wiki/ExtendingTemplates

This basically means you can have a ``base.html`` in your local templates folder
that extends Oscar's ``base.html`` but only customises the blocks that it needs
to.

Hence to customise ``base.html``, you can have an implementation like::

    # base.html
    {% extends 'oscar/base.html' %}

    ...

No real downsides to this one other than getting your front-end people to
understand it.

Overriding individual products partials
---------------------------------------

Apart from overriding ``catalogue/partials/product.html`` to change the look
for all products, you can also override it for individual product by placing
templates in ``catalogue/detail-for-upc-%s.html`` or
``catalogue/detail-for-class-%s.html`` to customise look on product detail
page and ``catalogue/partials/product/upc-%s.html`` or
``catalogue/partials/product/class-%s.html`` to tweak product rendering by
``{% render_product %}`` template tag , where ``%s`` is the product's UPC
or class's slug, respectively.

Example: Changing the analytics package
---------------------------------------

Suppose you want to use an alternative analytics package to Google analytics.
We can achieve this by overriding templates where the analytics urchin is loaded
and called.

The main template ``base.html`` has a 'tracking' block which includes a Google
Analytics partial.  We want to replace this with our own code.  To do this,
create a new ``base.html`` in your project that subclasses the original::

    # yourproject/templates/oscar/base.html
    {% extends 'oscar/base.html' %}

    {% block tracking %}
    <script type="javascript">
        ... [custom analytics here] ...
    </script>
    {% endblock %}

Doing this will mean all templates that inherit from ``base.html`` will include
your custom tracking.

