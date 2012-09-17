==============
Less Structure
==============

The Less files used here to generate the css in oscar/css.

Files in the root folder of oscar/less will render into their respective css counter parts.

Files in oscar/bootstrap and oscar/page are merged into styles.less

Responsive.less has mixins.less,osc_mixins.less and variables.less merged in but other than that is a stand alone file.

Dashboard.less is completly stand alone file to the other less files in the root folder oscar/less

* Notes based on less files are split into their separate folder names

Compiling less
--------------

Note :
  Only the files in the root folder oscar/less need to render into css files, other less files that may render into css
  files DO NOT need to be rendered into your project structure, they are redundent and may as well not be included in
  the project as they add confusion.


Bootstrap
---------

Files in the Bootstrap folder are direct copies from https://github.com/twitter/bootstrap/  - Version 2.0
These files have been kept clean of alterations so Bootstrap can be upgraded.
New projects however should feel free in modifying these to suit their designs.

Page
----





Dashboard
---------