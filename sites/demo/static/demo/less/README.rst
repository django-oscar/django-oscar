============
CSS and Less
============

Oscar uses Less to build its CSS files.  Each of the 3 main CSS files has a
corresponding less file::

    styles.less -> styles.css
    responsive.less -> responsive.css

Oscar's CSS uses Less files from `Twitter's Bootstrap project`_ - these are housed
in the bootstrap folder.

.. _`Twitter's Bootstrap project`: http://twitter.github.com/bootstrap/

Compiling less
--------------

Use the helper script to build the CSS files::
    
    ./generate_css.sh