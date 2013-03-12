===========
Conventions
===========

Make sure you've read http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html

Coding conventions
------------------

* Follow the Django conventions (http://docs.djangoproject.com/en/dev/internals/contributing/#coding-style)
* PEP8 (http://www.python.org/dev/peps/pep-0008/)
* PEP257 (http://www.python.org/dev/peps/pep-0257/)

General guidelines
------------------

The following are a set of design conventions that should be followed when
writing apps for Oscar:

* When referencing managers of model classes, use ``_default_manager`` rather than
  ``objects``.  This allows projects to override the default manager to provide
  domain-specific behaviour.


