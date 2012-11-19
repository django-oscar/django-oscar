========================================
My model customisations aren't picked up
========================================

Symptom
-------

You're trying to customise one of Oscar's models but your new fields don't seem
to get picked up.  For example, you are trying to add a field to the product
model 

Cause
-----

Oscar's models are being imported before your customised one.  Due to the way
model registration works with Django, the order in which models are imported is
important.  

Somewhere in your codebase is an import from ``oscar.apps.*.models``
that is being executed before your models are parsed.  

Solution
--------

Find and remove the import statement that is importing Oscar's models.  

In your overriding ``models.py``, ensure that you import Oscar's models *after*
your custom ones have been defined.

If other modules need to import these models then import from your local module,
not from Oscar directly.

Mailing list threads
--------------------

https://groups.google.com/forum/?fromgroups#!topic/django-oscar/oMdAB7zJLlI