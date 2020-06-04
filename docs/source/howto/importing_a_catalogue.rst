=====================
Importing a catalogue
=====================

.. warning::

   Handling imports works in Oscar, but the code quality of the importer is
   low as it is only used to populate the sandbox site, and not meant for
   general usage. So proceed at your own risk!

Importing a catalogue is pretty straightforward, and can be done in two easy
steps:

* Reading the catalogue CSV file, line by line, using ``csv.reader``.

* Using the info of each line, start by creating a ``Product`` object using the
  standard Django ORM, set the product attributes, save it, and finally set its
  ``ProductCategory``, ``Partner``, and ``StockRecord``.

Example
-------

An example of that is the ``CatalogueImporter`` used to import catalogues for
the sandbox site. The class is available under
``oscar.apps.partner.importers``.

Let's take a closer look at ``CatalogueImporter``::

    class CatalogueImporter(object):
        def __init__(self, logger):
            self.logger = logger

        @atomic
        def _import(self, file_path=None):
            ....

        def _import_row(self, row_number, row, stats):
            ....


The two steps procedure we talked about are obvious in this example, and are
implemented in ``_import`` and ``_import_row`` functions, respectively.

You can find an example of the CSV data that the ``CatalogueImporter``
expects `in the repository`_.

.. _`in the repository`: https://github.com/django-oscar/django-oscar/blob/master/sandbox/fixtures/books.essential.csv
