================================
How to configure stock messaging
================================

Stock messaging is controlled on a per-partner basis.  A product's stockrecord
has the following methods for messaging:

.. autoclass:: oscar.apps.partner.abstract_models.AbstractStockRecord
    :members: availability, availability_code

Both these methods delegate to a "partner wrapper" instance.  These are defined
in the ``OSCAR_PARTNER_WRAPPERS`` setting which is a dict mapping from partner
code to a class path, for instance::

    # settings.py
    OSCAR_PARTNER_WRAPPERS = {
        'partner-a': 'myproject.wrappers.PartnerAWrapper',
    }

The default wrapper is :class:`oscar.apps.partner.wrappers.DefaultWrapper`,
which provides methods of the same name.

.. autoclass:: oscar.apps.partner.wrappers.DefaultWrapper
    :members: availability, availability_code

Custom wrappers should subclass this class and override the appropriate methods.
Here's an example wrapper that provides custom availability messaging::

    # myproject/wrappers.py
    from oscar.apps.partner import wrappers


    class PartnerAWrapper(wrappers.DefaultWrapper):
        
        def availability(self, stockrecord):
            if stockrecord.net_stock_level > 0:
                return "Available to buy now!"
            return "Sorry, not available"

        def availability_code(self, stockrecord):
            if stockrecord.net_stock_level > 0:
                return "icon_tick"
            return "icon_cross"
