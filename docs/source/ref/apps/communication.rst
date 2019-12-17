=============
Communication
=============

The Communication app is used to manage emails and notifications to users.
If ``OSCAR_SAVE_SENT_EMAILS_TO_DB`` is ``True``, then all sent emails
are saved to the database as instances of ``oscar.apps.communication.models.Email``

The ``Dispatcher`` class from ``oscar.apps.communication.utils`` is used to send
emails and notifications.

Abstract models
---------------

.. automodule:: oscar.apps.communication.abstract_models
    :members:

Utils
-----

.. automodule:: oscar.apps.communication.utils
    :members:
