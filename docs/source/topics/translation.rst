===========
Translation
===========

All Oscar translation work is done on Transifex_. If you'd like to contribute,
just apply for a language and go ahead!

.. _Transifex: https://www.transifex.com/projects/p/django-oscar/


Translating Oscar within your project
-------------------------------------

If Oscar does not provide translations for your language, or if you want to
provide your own, do the following.

Within your project, create a locale folder and a symlink to Oscar so that
``./manage.py makemessages`` finds Oscar's translatable strings::

    mkdir locale i18n
    ln -s $PATH_TO_OSCAR i18n/oscar
    ./manage.py makemessages --symlinks --locale=de

This will create the message files that you can now translate.
