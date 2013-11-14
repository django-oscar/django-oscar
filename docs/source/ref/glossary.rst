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

       .. seealso:: `Wikipedia: Stock-keeping unit <http://en.wikipedia.org/wiki/Stock-keeping_unit>`_

    UPC
    Universal Product Code
       A code uniquely identifying a product worldwide.

       .. seealso:: `Wikipedia: Universal Product Code <http://en.wikipedia.org/wiki/Universal_Product_Code>`_

    Product Range

       A range is a subset of the product catalogue. It's another way of
       defining groups of products other than categories and product classes.

       An example would be a book shop which might define a range of "Booker
       Prize winners".  Each product will belong to different categories within
       the site so ranges allow them to be grouped together.

       Ranges can then be used in offers (eg 10% off all booker prize winners).
       At some point, ranges will be expanded to have their own detail pages
       within Oscar too.​


    Product Class

        Used for defining
        :class:`options <oscar.apps.catalogue.abstract_models.AbstractOption>`
        and
        :class:`attributes <oscar.apps.catalogue.abstract_models.AbstractProductAttribute>`
        for a subset of products.
        For instance, product classes could be Books, DVDs, and Toys.
        A product can only belong to one product class.

    Product Category

        Categories and subcategories are used to organise your catalogue.
        They're merely used for navigational purposes; no logic in Oscar cares
        about the category.
        For instance, if you're a book shop, you could have categories such as
        fiction, romance, and children's books. If you'd sell both books and
        e-books, they could be of a different :term:`Product Class`, but in the
        same category.
