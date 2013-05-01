========
Glossary
========

This is a work-in-progress list of commonly used terms when discussing Oscar.

.. glossary::
    :sorted:

    Partner
    Fulfillment partner
       An individual or company who can fulfil products. E.g. for physical
       goods, somebody with a warehouse and means of delivery.

       .. seealso:: Related model: :class:`oscar.apps.partner.abstract_models.AbstractPartner`

    SKU
    Stock-keeping unit.
       A :term:`partner`'s way of tracking her products. Uniquely identifies a
       product in the partner's warehouse. Can be identical to the products
       :term:`UPC`. It's stored as an attribute of
       :attr:`StockRecord <oscar.apps.partner.abstract_models.AbstractStockRecord.partner_sku>`

       .. seealso:: `Wikipedia <http://http://en.wikipedia.org/wiki/Stock-keeping_unit>`_

    UPC
    Universal Product Code
       A code uniquely identifying a product worldwide.

       .. seealso:: `Wikipedia <http://en.wikipedia.org/wiki/Universal_Product_Code>`_


