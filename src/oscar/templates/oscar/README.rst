==================
Template Structure
==================

Markup
------

Template markup for the most part has been written in accordance with Twitter Bootstrap.
Documentation on Bootstrap HTML markup and classes used see (http://twitter.github.com/bootstrap/index.html).

Layouts
-------

Currently there are 5 different layouts that extend the base.html

layout.html :
    For single column layouts
* detail.html
* basket.html
* flatpages/default.html

layout_2_col.html :
    For two column layouts whereby first column is subservient (aside) to the main column
* home.html
* browse.html

layout_3_col.html :
    For three column layouts whereby first and third columns are subservient (aside) to the main middlecolumn
* Currently NOT used

checkout/layout.html :
  For the checkout pages, removes the main navigation and uses a single column by default
* checkout.html
* gateway.html
* thank_you.html

dashboard/layout.html :
  For dashboard section specifically different from the other frontend features:
* separate css
* separate js
* single column 100% page width

Forms
-----

Forms are rendered using either of these two partial templates

* form_fields.html
* form_fields_inline.html

form_fields.html :
    This is used for the majority of the forms in the frontend and dashboard, using a horizontal label / field stack

form_fields_inline.html :
    Used for smaller forms to reduced screen space (mainly in the dashboard section for search forms)

Partials form_fields::

    'include "partials/form_fields.html" with form=form'

Partials form_fields_inline::

    'include "partials/form_fields_inline.html" with form=form'

Conventions
-----------

Template names should use underscores, not hyphens.
