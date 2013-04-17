==========================================
How to do a dashboard for multiple dealers
==========================================

The use case is a website where dealers sign up for the website and can then
add and manage their and only their products. This is different from a stock
Oscar install, because by default, the dashboard allows managing all products.

Lingo
-----
Dealers are understood to be users who have an associated partner instance. You
can still have normal users.

Make the connection
-------------------
Replace the Partner model. AbstractPartner already carries a ``ManyToManyField``
to users, which you can use. I opted to replace that field with a
``OneToOneField``.
You'll need to enforce creating of a ``StockRecord`` with every ``Product``.
When a ``Product`` is created, ``Stockrecord.partner`` gets set to
``self.request.user.partner`` (created if necessary), and hence the connection
is made.

Filter the dashboard
--------------------
Every view that returns a list of products needs to be adapted to only return
products that belong to the dealer::

    # views.py
    class FilteredProductListView(ProductListView):

        def get_queryset(self):
            qs = super(FilteredProductListView, self).get_queryset()
            partner = self.request.user.partner
            return qs.filter(stockrecord__partner=partner)

This could turn into quite a bit of work.
Luckily most deployments will use a heavily reduced dashboard, consequently
reducing the necessary work.

Decorators
----------

Dashboard access is limited to staff users by default. You'll need to replace
the decorators with a ``login_required`` decorator.

Dashboard navigation
--------------------

Can be adjusted by tweaking the ``OSCAR_DASHBOARD_NAVIGATION`` setting.