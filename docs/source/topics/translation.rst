.. spelling::

    Transifex

===========
Translation
===========

All Oscar translation work is done on Transifex_. If you'd like to contribute,
just apply for a language and go ahead!
The source strings in Transifex are updated after every commit on Oscar's
master branch on GitHub. We only pull the translation strings back into Oscar's
repository when preparing for a release. That means your most recent
translations will always be on Transifex, not in the repository!

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
