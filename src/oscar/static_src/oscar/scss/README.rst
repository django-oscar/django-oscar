============
CSS and SCSS
============

Oscar uses SCSS to build its CSS files. Each of the 2 main CSS files has a
corresponding scss file::

    styles.scss -> styles.css
    dashboard.scss -> dashboard.css

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
