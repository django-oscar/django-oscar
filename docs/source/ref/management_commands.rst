===================
Management commands
===================

``oscar_fork_app <applabel> <folder>``
--------------------------------------

Creates a local version of one of Oscar's core apps so it can be customised.

A new python package will be created in the specified folder with a
``models.py`` module and a folder of migrations.

``oscar_fork_statics <folder>``
-------------------------------

Copies Oscar's static files into the specified folder so they can be
customised.

``oscar_calculate_scores``
--------------------------

Calculates product scores and updates each 
:class:`~oscar.apps.analytics.models.ProductRecord` instance.

``oscar_cleanup_alerts``
-------------------------------

``oscar_find_duplicate_emails``
-------------------------------

``oscar_generate_email_content``
--------------------------------

``oscar_import_catalogue``
--------------------------

``oscar_import_catalogue_images``
---------------------------------

``oscar_send_alerts``
---------------------

``oscar_update_product_ratings``
--------------------------------

