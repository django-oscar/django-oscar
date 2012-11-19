Quick start
===========

We can do this quickly.  Create a virtualenv using virtualenvwrapper and
install Django and django-oscar::

    mkvirtualenv --no-site-packages vanilla
    pip install Django django-oscar

Take a copy of the sample settings file, found at::

    https://github.com/tangentlabs/django-oscar/blob/master/examples/vanilla/settings_quickstart.py

Import the sample products and images::

    wget https://github.com/tangentlabs/django-oscar/blob/master/examples/sample-data/books-catalogue.csv
    python manage.py import_catalogue books-catalogue.csv

    wget https://github.com/tangentlabs/django-oscar/blob/master/examples/sample-data/book-images.tar.gz
    python manage.py import_images book-images.tar.gz

And there you have it: a fully functional e-commerce site with a product range of 100 popular books.





For
instance, if every product in your shop has an associated video, then
Oscar lets you add such a field to your core product model.  You don't
have to model your domain logic using the `Entity-Attribute-Value`_ pattern or
other such meta-nastiness - your core models should reflect the specifics of
your domain.

.. _`Entity-Attribute-Value`: http://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model
