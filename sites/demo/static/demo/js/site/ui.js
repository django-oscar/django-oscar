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
          slideshow: true
        });
    }

    function productImageCarousel() {
        $('#product-image-carousel').flexslider({
          animation: "slide"
        });
    }

    function productSingleCarousel() {
        $('.product-single-carousel .flexslider').flexslider({
          animation: "slide"
        });
    }

    function productAffix() {
        $('.product-gallery').affix();
    }

    function productCarousel() {
        $('.product-carousel .flexslider').each(function(){
            var productPage = $('.product-page'),
                homePage = $('.home-page'),
                offerPage = $('.offer-page'),
                imageWidth = 180,
                maxProducts = 4,
                minProducts = 1,
                showNav = true;
            if (productPage.length > 0) {
                imageWidth = 150;
                maxProducts = 5;
                showNav = false;
                minProducts = 2;
            }
            if (homePage.length > 0) {
                imageWidth = 140;
            }
            if (offerPage.length > 0) {
                imageWidth = 150;
                maxProducts = 5;
            }
            $(this).flexslider({
                animation: "slide",
                animationLoop: true,
                itemWidth: imageWidth,
                minItems: minProducts,
                maxItems: maxProducts,
                controlNav: showNav
            });
        });
    }

    function matchHeight(hasChanged) {
      if (!hasChanged) {
        return;
      }
      var matchHeight = $('[data-behaviours~="match-height"]');

      if(matchHeight.length > 1) {
        var rowHeight = matchHeight.closest('.row-fluid').height() - 40;

        matchHeight.each(function() {
          $(this).css('min-height', rowHeight);
        });
      }    
    }


    // Register modernizr function against all viewports
    site.responsive.register(svgModernizr);
    site.responsive.register(productImageCarousel);

    // Register mobile callback


    // Register desktop callback
    site.responsive.register(matchHeight, ['desktop', 'tablet']);
    site.responsive.register(megaCarousel, ['desktop', 'tablet']);
    site.responsive.register(productCarousel, ['desktop', 'tablet']);
    site.responsive.register(productSingleCarousel, ['desktop', 'tablet']);

}(site, jQuery));