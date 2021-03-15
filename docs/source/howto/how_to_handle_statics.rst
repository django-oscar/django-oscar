.. spelling::

    NGINX
    Gulp

================================
How to change Oscar's appearance
================================

This is a guide for Front-End Developers (FEDs) working on Oscar projects, not
on Oscar itself.  It is written with Tangent's FED team in mind but should be
more generally useful for anyone trying to customise Oscar and looking for the
right approach.

Overview
========

Oscar ships with a set of HTML templates and a collection of static files
(e.g. images and Javascript).  Oscar's default CSS is generated from SASS
files.

Templates
---------

Oscar's default templates use the mark-up conventions from the Bootstrap
project. Classes for styling should be separate from classes used for
Javascript. The latter must be prefixed with ``js-``, and using data attributes
is often preferable.

Frontend vs. Dashboard
----------------------

The frontend and dashboard are intentionally kept separate. They incidentally
both use Bootstrap and Font Awesome, but may be updated individually.

For the frontend, ``styles.scss`` imports Bootstrap and Font Awesome SASS
stylesheets, and ties them together with Oscar-specific styling.

For the dashboard, ``dashboard.scss`` also imports Bootstrap and Font Awesome
SASS stylesheets, and adds Oscar-specific customisations.

SCSS/CSS
--------

CSS files served to the browser are compiled from their SASS sources. For
local development, :command:`npm run watch` will watch for local changes to SASS files and
automatically rebuild the compiled CSS.

Use the command :command:`make assets` to compile assets manually.

Javascript
----------

Oscar uses Javascript for progressive enhancements. This guide used to document
exact versions, but quickly became outdated. It is recommended to inspect
``layout.html`` and ``dashboard/layout.html`` for what is currently included.

Customisation
=============

Customising templates
---------------------

Oscar ships with a complete set of templates (in ``oscar/templates``).  These
will be available to an Oscar project but can be overridden or modified.

The templates use Bootstrap conventions for class names and mark-up.

There is a separate recipe on how to do this.

Customising statics
-------------------

Oscar's static files are stored in ``oscar/static``.  When a Django site is
deployed, the ``collectstatic`` command is run which collects static files from
all installed apps and puts them in a single location (called the
``STATIC_ROOT``).  It is common for a separate HTTP server (like NGINX) to be
used to serve these files, setting its document root to ``STATIC_ROOT``.

For an individual project, you may want to override Oscar's static files.  The
best way to do this is to have a statics folder within your project and to add
it to the ``STATICFILES_DIRS`` setting.  Then, any files which match the same
path as files in Oscar will be served from your local statics folder instead.
For instance, if you want to use a local version of ``oscar/css/styles.css``,
your could create a file::

    yourproject/
        static/
            oscar/
                css/
                    styles.css

and this would override Oscar's equivalent file.

To make things easier, Oscar ships with a management command for creating a copy
of all of its static files.  This breaks the link with Oscar's static files and
means everything is within the control of the project.  Run it as follows::

    # with default "target_path" of "static"
    ./manage.py oscar_fork_statics

or

    # with custom "target_path"
    ./manage.py oscar_fork_statics /path/to/static/directory/

This is the recommended approach for non-trivial projects.

Another option is simply to ignore all of Oscar's CSS and write your own from
scratch.  To do this, you simply need to adjust the layout templates to include
your own CSS instead of Oscar's.  For instance, you might override ``oscar/layout.html``
and replace the ``styles`` block::

    # project/oscar/layout.html
    {% extends "oscar/layout.html" %}
    {% load static %}

    {% block styles %}
        <link rel="stylesheet" type="text/css" href="{% static 'myproject/styles.css' %}" />
    {% endblock %}
