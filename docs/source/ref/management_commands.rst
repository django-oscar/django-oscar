===================
Management commands
===================

``oscar_fork_app <applabel> <folder>``
--------------------------------------

Creates a local version of one of Oscar's core apps so it can be customised.

A new python package will be created in the specified folder with 
``models.py`` and ``admin.py`` modules and a folder of migrations. Once the
command has been run, the new app needs to be added to ``INSTALLED_APPS`` to
replace the core version.

For example, if you want to customise shipping, run:

.. source-code:: bash

   $ ./manage.py oscar_fork_app shipping myproject/

which will create a ``myproject/shipping`` folder with the appropriate contents.
Finally adjust your settings to include this new app in ``INSTALLED_APPS`` and
you're ready to start customising.

.. source-code:: bash

    # settings.py
 
    INSTALLED_APPS = [
        ...
    ]
    from oscar import get_core_apps
    INSTALLED_APPS = INSTALLED_APPS + get_core_apps([
        'myproject.shipping'])


``oscar_fork_statics <folder>``
-------------------------------

Copies Oscar's static files into the specified folder so they can be
customised.

This allows projects to use Oscar's LESS files as a starting point for their own
customisation.

Note that new folder must be added to the ``STATICFILES_DIRS`` setting.


``oscar_calculate_scores``
--------------------------

Calculates product scores and updates each 
:class:`~oscar.apps.analytics.models.ProductRecord` instance. The command
employs the
:class:`~oscar.apps.analytics.scores.Calculator` class to perform the
calculation and update. Override this class to alter how scores are calculated.


``oscar_send_alerts``
---------------------

Send product alerts.

This command looks for all products that have active stock alerts and then
iterates through each and sends an email and a site notification if the product
is now available to the user who created the alert.


``oscar_cleanup_alerts``
-------------------------------

Remove unconfirmed product alerts older than a given age.

Options:

- ``--days`` Specify the age threshold in days;
- ``--hours`` Specify the age threshold in hours.

If no options are passed, an age threshold of 24 hours is used.

Oscar allows customers to register for an email notification when a product is
out of stock.  Anonymous customers are required to click a confirmation link in
an email before the alert is 'active'. Of course, some customers will trigger
the alert email but not click the link leading to stale, unconfirmed alerts.  
This command provides a means to delete such alerts.


``oscar_generate_email_content <type> <order-number>``
------------------------------------------------------

Prints out the email subject and body for a given event type and order number.

This command is for debugging email template generation. It is called by passing
in a communication event type (eg ``ORDER_PLACED``) and the number of an order.
The command prints the subject, text body and HTML body of the email to the
console.

Example usage:

.. code-block:: bash

   $ ./manage.py oscar_generate_email_content ORDER_PLACED 100001


``oscar_update_product_ratings``
--------------------------------

Update all product ratings.

This command iterates over all products and calls the ``update_rating`` method
on each, which updates the ``rating`` field.
