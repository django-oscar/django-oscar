=====================
Importing a catalogue
=====================

.. warning::

   Handling imports works in Oscar, but the code quality of the importers is
   low as they are only used to populate the sandbox and demo site, and not
   meant for general usage. So proceed at your own risk!

Importing a catalogue is pretty straightforward, and can be done in two easy
steps:

* Reading the catalogue CSV file, line by line, using ``UnicodeCSVReader``.
  ``oscar.core.compat.UnicodeCSVReader`` is a Unicode compatible wrapper for
  CSV reader and writer that abstracts away differences between Python 2 and 3.

* Using the info of each line, start by creating a ``Product`` object using the
  standard Django ORM, set the product attributes, save it, and finally set its
  ``ProductCategory``, ``Partner``, and ``StockRecord``.

Example
-------

Two examples of that are ``CatalogueImporter`` and ``DemoSiteImporter``, used
to import catalogues for the sandbox and demo-site, respectively. Both classes
are available under ``oscar.apps.partner.importers``.

Let's take a closer look at ``DemoSiteImporter``::

    class DemoSiteImporter(object):
        def __init__(self, logger):
            self.logger = logger
    
        @atomic
        def handle(self, product_class_name, filepath):
            ....
    
        def create_product(self, product_class, attribute_codes, row):  # noqa
            ....
            

The two steps procedure we talked about are obvious in this example, and are
implemented in ``handle`` and ``create_product`` functions, respectively.

Start by initializing the class with a logger, and call ``handle`` with
``product_class_name`` and ``filepath`` arguments. There's absolutely no need
to hard-code ``product_class_name`` and make product-class unified for all
products like this example does, you can make it part of the CSV file content.
``handle`` then calls ``create_product`` once for every line, and the latter
uses Django ORM to create a couple of objects to represent the product and its
properties.
