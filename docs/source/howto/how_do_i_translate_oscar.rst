=========================
How do I translate Oscar?
=========================

Before doing any translation work, ensure you are famility with `Django's i18n
guidelines`_.

.. _`Django's i18n guidelines`: https://docs.djangoproject.com/en/dev/topics/i18n/

Contributing translations to Oscar
----------------------------------

To submit a new set of translations for Oscar, do the following:

1. Fork the repo and install Oscar's repo then navigate to the ``oscar``
   folder::

    git clone git@github.com:$USERNAME/django-oscar.git
    cd django-oscar/
    mkvirtualenv oscar
    make sandbox

2. Generate the message files for a given language::

    django-admin.py makemessages --locale=$LANGUAGE_CODE

3. Use the Rosetta_ functionality within the sandbox to add translations for the
   new messages files.::

    cd sites/sandbox
    ./manage.py runserver
    open http://localhost:8000/rosetta

.. _Rosetta: https://github.com/mbi/django-rosetta

4. Send a pull request!::

    git checkout -b new-translation
    git add oscar/locale
    git commit
    git push origin new-translation

Your work will be much appreciated.

Translating Oscar within your project
-------------------------------------

If Oscar does not provide translations for your language, or if you want to
provide your own, do the following.

Within your project, create a locale folder and a symlink to Oscar so that ``./manage.py
makemessages`` finds Oscar's translatable strings::

    mkdir locale i18n
    ln -s $PATH_TO_OSCAR i18n/oscar
    ./manage.py makemessages --symlinks --locale=de

This will create the message files that you can now translate.
