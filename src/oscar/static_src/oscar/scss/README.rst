============
CSS and SCSS
============

Oscar uses SCSS to build its CSS files. Each of the 3 main CSS files has a
corresponding scss file::

    styles-bootstap4.scss -> styles-bootstap4.css
    dashboard-bootstap4.scss -> dashboard-bootstap4.css

Oscar's CSS uses SCSS files from the `Bootstrap project`_ - these are housed
in the bootstrap folder.

.. _`Bootstrap project`: http://getbootstrap.com/

Developing SCSS
---------------

You can watch changes to SCSS from the root of the project using npm::

    npm run watch

Compiling SCSS
--------------

You can compile the CSS from the root of the project using a make target::

    make assets

