=======================
How to customise a view
=======================

Oscar has many views. This How-to describes how to one of them for your project.
It builds upon the steps described in :doc:`/topics/customisation`. Please
read it first and ensure that you've:

* Created an app with the same label
* Overridden the Oscar app with your own
* Created a custom ``app.py``

Example
-------

Create a new homepage view class in ``myproject.promotions.views`` - you can subclass
Oscar's view if you like::

    from oscar.apps.promotions.views import HomeView as CoreHomeView

    class HomeView(CoreHomeView):
        template_name = 'promotions/new-homeview.html'

In this example, we set a new template location but it's possible to customise the view
in any imaginable way.

Now you can hook it up in your local ``app.py``::

    # myproject/promotions/app.py
    from oscar.apps.promotions import PromotionsApplication as CorePromotionsApplication

    from myproject.promotions.views import HomeView

    class PromotionsApplication(CorePromotionsApplication):
        home_view  = HomeView

    application = PromotionsApplication()
