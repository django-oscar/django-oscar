===========
Oscar sites
===========

Oscar ships with two working Django projects that use Oscar:

Sandbox
-------

This is a vanilla install of Oscar with as little customisation as possible to
get a basic site working.  It's really intended for local development and QA.

It does have a few customisations:

* A "gateway" page that lets users create a dashboard user so they can play with
  the dashboard.
* A profile model with a few fields, designed to test Oscar's account section
  which should automatically allow the profile fields to be edited.

It is deployed hourly to: http://latest.oscarcommerce.com
