========
Glossary
========

This is a work-in-progress list of commonly used terms when discussing Oscar.

.. glossary::
    :sorted:

    Partner
    Fulfilment partner
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

       Ranges can then be used in offers (e.g. 10% off all Booker prize winners).
       At some point, ranges will be expanded to have their own detail pages
       within Oscar too.


    Product Class

        Product classes are an important concept in Oscar. Each product is
        assigned to exactly one product class. For instance, product classes
        could be Books, DVDs, and Toys.

        Settings on a product class decide whether stock levels are
        :attr:`tracked <oscar.apps.catalogue.abstract_models.AbstractProductClass.track_stock>`
        for the associated products, and whether they
        :attr:`require shipping <oscar.apps.catalogue.abstract_models.AbstractProductClass.requires_shipping>`.
        So if you have products that require shipping and ones which don't,
        you'll need at least two product classes.

        Used for defining
        :class:`options <oscar.apps.catalogue.abstract_models.AbstractOption>`
        and
        :class:`attributes <oscar.apps.catalogue.abstract_models.AbstractProductAttribute>`
        for a subset of products.

    Product Category

        Categories and subcategories are used to semantically organise your
        catalogue. They're merely used for navigational purposes; no business
        logic in Oscar considers a product's category.
        For instance, if you're a book shop, you could have categories such as
        fiction, romance, and children's books. If you'd sell both books and
        e-books, they could be of a different :term:`Product Class`, but in the
        same category.

    Product Options

        Options are values that can be associated with a item when it is added
        to a customer's basket.  This could be something like a personalised
        message to be printed on a T-shirt, or a colour choice.

        Product Options are different from Product Attributes in that they are
        used to specify a specific purchase choice by the customer, whereas
        Attributes exist to store and display the features of a product in
        a structured way.
