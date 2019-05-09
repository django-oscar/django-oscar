=============
Communication
=============

Communication app used to work with emails and notifications.
If the ``OSCAR_SAVE_SENT_EMAILS_TO_DB`` setting is ``True`` (default value),
then all sent emails will be saved to database (as instances of
``oscar.apps.communication.models.Email`` model).

``Dispatcher`` class from ``oscar.apps.communication.utils`` used to send
emails and notifications.

Abstract models
---------------

.. automodule:: oscar.apps.communication.abstract_models
    :members:

Utils
-----

.. automodule:: oscar.apps.communication.utils
    :members:
