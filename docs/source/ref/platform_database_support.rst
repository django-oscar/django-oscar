=============================
Platform and database support
=============================

Operating system
================

Oscar does not support for Microsoft Windows. Some of Oscar's dependencies don't support Windows and/or are
tricky to install properly in that environment, and therefore you might encounter some errors that prevent a
successful installation. Contributions to improve support for Windows are welcome.


Databases
=========

Oscar officially supports PostgreSQL. Oscar is likely to work with the following databases, but official support is
not provided for them:

* MariaDB
* Oracle
* SQLite (this is suitable only for use in development)

Oscar does not support MySQL. Developers are likely to encounter issues related to Unicode handling and update queries
for certain query types. Both issues are caused by limitations in MySQL itself, or in Django's ORM support for MySQL.
Relevant discussions on Django project are:

* `Make MySQL backend default to utf8mb4 encoding <https://code.djangoproject.com/ticket/18392>`_.
* `QuerySet.update() fails on MySQL if a subquery references the base table <https://code.djangoproject.com/ticket/28787>`_.
