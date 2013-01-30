=====================
How to handle statics
=====================

Oscar ships with HTML templates, 

The templates use the following CSS files:

CSS
---

base.html
* oscar/static/oscar/css/styles.css
* oscar/static/oscar/css/responsive.css

dashboard/layout.html
* oscar/static/oscar/css/dashboard.css
* oscar/static/oscar/js/bootstrap-wysihtml5/bootstrap-wysihtml5.css

catalogue/detail.html
* oscar/js/colorbox/colorbox.css

Javascript
----------

base.html
* jQuery 1.7.2 (from Google CDN)
* oscar/js/jquery/jquery.easing.1.3.js
* oscar/js/bootstrap/bootstrap.min.js

basket/basket.html
* oscar/js/oscar/checkout.js

partials/extrascripts.html
* oscar/js/elastislide/jquery.elastislide.js
* oscar/js/colorbox/jquery.colorbox-min.js
* oscar/js/responsivegallery/jquery.tmpl.min.js
* oscar/js/responsivegallery/gallery.js - custom gallery script
* oscar/js/oscar/ui.js

checkout/layout.html
* oscar/js/oscar/ui.js
* oscar/js/oscar/checkout.js

dashboard/layout.html
* oscar/js/plugins/plugins.js
* oscar/js/bootstrap-wysihtml5/wysihtml5.min.js
* oscar/js/bootstrap-wysihtml5/bootstrap-wysihtml5.min.js
* oscar/js/oscar/ui.js
* oscar/js/oscar/dashboard.js
* jQuery UI 1.8.23 (from Google CDN)
