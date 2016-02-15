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
(eg images, javascript).  Oscar's default CSS is generated from LESS
files.

Templates
---------

Oscar's default templates use the mark-up conventions from the Bootstrap
project. Classes for styling should be separate from classes used for
Javascript. The latter must be prefixed with ``js-``, and using data attributes
is often preferable.

Frontend vs. Dashboard
----------------------

The frontend and dashboard are intentionally kept very separate. They
incidentally both use Bootstrap, but may be updated individually.
The frontend is based on Bootstrap's LESS files and ties it together with
Oscar-specific styling in ``styles.less``.

On the other hand, ``dashboard.less`` just contains a few customisations that
are included alongside a copy of stock Bootstrap CSS - and at the time of
writing, using a different Bootstrap version.

LESS/CSS
--------

By default, CSS files compiled from their LESS sources are used rather than the
LESS ones.  To use Less directly, set ``USE_LESS = True`` in your settings file.
This will enable the on-the-fly pre-processor which lets you trial changes with
a page reload. If you want to commit your changes, use the ``make css`` Makefile
command, making sure you have the ``lessc`` binary available on your command line.
A few other CSS files are used to provide styles for javascript libraries.

Javascript
----------

Oscar uses javascript for progressive enhancements. This guide used to document
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
``STATIC_ROOT``).  It is common for a separate HTTP server (like nginx) to be
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

    ./manage.py oscar_fork_statics

This is the recommended approach for non-trivial projects.

Another option is simply to ignore all of Oscar's CSS and write your own from
scratch.  To do this, you simply need to adjust the layout templates to include
your own CSS instead of Oscar's.  For instance, you might override ``base.html``
and replace the 'less' block::

    # project/base.html

    {% block less %}
        <link rel="stylesheet" type="text/less" href="{{ STATIC_URL }}myproject/less/styles.less" />
    {% endblock %}

