/*jslint browser:true */
/*global jQuery, Modernizr, site: false */

(function (site, $) {
    "use strict";

    function svgModernizr() {
        if (!Modernizr.svg) {
            $(".logo").attr("src", "/static/demo/img/svg/logo.png");
        }
    }

    function megaCarousel() {
        $('#homepage-carousel').flexslider({
          animation: "fade",
          slideshow: true,
        });
    }


    // Register modernizr function against all viewports
    site.responsive.register(svgModernizr);

    // Register mobile callback


    // Register desktop callback
    site.responsive.register(megaCarousel, ['desktop', 'tablet']);

}(site, jQuery));