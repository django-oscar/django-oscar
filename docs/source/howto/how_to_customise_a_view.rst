=================================
How to customise an existing view
=================================

Oscar has many views. This How-to describes how to customise one of them for
your project.  It builds upon the steps described in
:doc:`/topics/customisation`. Please read it first and ensure that you've:

* Created a Python module with the the same label
* Added it as Django app to ``INSTALLED_APPS``
* Added a ``models.py`` and ``admin.py``

Example
-------

Create a new homepage view class in ``myproject.offer.views`` - you can
subclass Oscar's view if you like::

    from oscar.apps.offer.views import OfferListView as CoreOfferListView

    class OfferListView(CoreOfferListView):
        template_name = 'offer/new_list.html'

In this example, we set a new template location but it's possible to customise
the view in any imaginable way.
As long as the view has the same name as the view you're replacing, and is in
an app with the same name, it will get picked up automatically by Oscar.

If you want to change the template, create the alternative template
``new_list.html``.  This could either be
in a project-level ``templates`` folder that is added to your ``TEMPLATE_DIRS``
settings, or a app-level ``templates`` folder within your 'offer' app.