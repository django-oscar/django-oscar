=======
Statics
=======

Oscar ships with a set of static files (js/css/less/images).  These are used on
the sandbox site.  

When building your own project, it is not recommended to use these files
straight from the package.  Rather, you should take a static copy of the
``oscar/static/oscar`` folder and commit it into your project.  

This is because the link with upstream project is not really helpful for
statics.  When you upgrade Oscar, the updated CSS files may not work with your
mark-up, causing unnecessary work on your behalf.  It's better to have complete
control of the statics within your project.
