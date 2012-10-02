var oscar = oscar || {};
oscar.messages = {
    addMessage: function(tag, msg) {
        var msgHTML = '<div class="alert fade in alert-' + tag + '">' +
        '<a class="close" data-dismiss="alert">x</a>' + msg +
        '</div>';
        $('#messages').append($(msgHTML));
    },
    debug: function(msg) { oscar.messages.addMessage('debug', msg); },
    info: function(msg) { oscar.messages.addMessage('info', msg); },
    success: function(msg) { oscar.messages.addMessage('success', msg); },
    warning: function(msg) { oscar.messages.addMessage('warning', msg); },
    error: function(msg) { oscar.messages.addMessage('error:', msg); }
};
oscar.forms = {
    init: function() {
        // Forms with this behaviour are 'locked' once they are submitted to
        // prevent multiple submissions
        $('form[data-behaviours~="lock"]').submit(oscar.forms.submitIfNotLocked);
    },
    submitIfNotLocked: function(event) {
        $form = $(this);
        if ($form.data('locked')) {
            return false;
        }
        $form.data('locked', true);
    }
};
$(function(){oscar.forms.init();});

$(document).ready(function()
{
    // Product star rating  -- must improve this in python
    $('.product_pod, .span6, .promotion_single').each(function()
    {
        var sum_total_reviews = $(this).find(".review_count li").length * 5,
            sum_rating_count = 0;
        $(this).find('.review_count li').each(function()
        {
            sum_rating_count += parseFloat($(this).text());
        });
        var ave_rating = sum_rating_count / sum_total_reviews *10;
        if (ave_rating <= 2) {
            ave_rating = 'One';
        } else if (ave_rating <= 4) {
            ave_rating = 'Two';
        } else if (ave_rating <= 6) {
            ave_rating = 'Three';
        } else if (ave_rating <= 8) {
            ave_rating = 'Four';
        } else if (ave_rating <= 10) {
            ave_rating = 'Five';
        }
        $(this).find('.review_count')
          .after('<p class=\"star ' + ave_rating + '\">' + ave_rating + ' star(s) by user reviews. <a href=\"#reviews\">Add review</a></p>')
          .remove();
    });
    // Product star rating each review -- must improve this in python
    $('.review').each(function()
    {
        var user_rating = 0;
        $(this).find('span').each(function()
        {
            user_rating += parseFloat($(this).text());
        });
        if (user_rating == 1) {
            user_rating = 'One';
        }
        else if (user_rating == 2) {
            user_rating = 'Two';
        }
        else if (user_rating == 3) {
            user_rating = 'Three';
        }
        else if (user_rating == 4) {
            user_rating = 'Four';
        }
        else if (user_rating == 5) {
            user_rating = 'Five';
        }
        $(this).find('h3').addClass(user_rating).end().find('span').remove();
    });

    var window_width = $(window).width(), // Width of the window
        $sidebar = $('aside.span3'), // Width of main navigation
        $browse = $('#browse > .dropdown-menu'), // Height of main navigation
        $browse_open = $browse.parent().find('> a[data-toggle]');

        if (window_width > 480) {
            // This activates elastislide
            var es_carousel = $('.es-carousel-wrapper'),
            product_page = $('.product_page').length;
            // on prodct page
            if (es_carousel.length && product_page > 0) {
                es_carousel.elastislide({
                    imageW: 175,
                    minItems: 5,
                    onClick:  true
                });
                // This activates colorbox on the product page
                var lightbox_elements = $('a[rel=lightbox]');
                if (lightbox_elements.length) {
                    lightbox_elements.colorbox();
                }
            } else if (es_carousel.length) {
                es_carousel.elastislide({
                    imageW: 200,
                    minItems: 4,
                    onClick:  true
                });
            }
        }

    if (window_width > 980) {
      // set width of nav dropdown on the homepage
      $browse.css('width', $sidebar.outerWidth());
      // Remove click on browse button if menu is currently open
      if  ($browse_open.length < 1) {
        $browse.parent().find('> a').on('click', function()
        {
          return false;
        });
        // set margin top of aside allow space for open navigation
        $sidebar.css({
          marginTop: $browse.outerHeight()
        });
      }
    }

    // This activates the promotional banner carousel
    $('#myCarousel').carousel({
        interval: 6000
    });

    // This activates the Typeahead function in the search
    $('.typeahead').typeahead();

    // Acordion - remove the first in the list as it is duplication.
    var n = $('.accordion dt').length;
    if (n > 1) {
        $('.accordion dt:first, .accordion dd:first,').hide();
    }
    // Acordion
    $('.accordion dd').each(function(index)
    {
        $(this).css('height', $(this).height());
    });
    $(".accordion dt").click(function(){
        $(this).next("dd").slideToggle("slow").siblings("dd:visible").slideUp("slow");
        $(this).toggleClass("open");
        $(this).siblings("dt").removeClass("open");
    });
    $(".accordion dd").hide();

    /* scroll to sections */
    $('.top_page a').click(function (e) {
        var section = $(this).attr('href');
        var sectionPosition = Math.floor($(section).offset().top);
        var currentPosition = Math.floor($(document).scrollTop());
        // when scrolling downwards
        if (sectionPosition > currentPosition) {
            $('html, body').animate({
                scrollTop: sectionPosition}, 500, function() {
                $('html, body').animate({
                    scrollTop: sectionPosition
                });
            });
        }
        // when scrolling upwards
        else if (sectionPosition < currentPosition) {
            $('html, body').animate({
                scrollTop: sectionPosition}, 500, function() {
                $('html, body').animate({
                    scrollTop: sectionPosition
                });
            });
        }
        e.preventDefault();
    });

    //For IE - sets the width of a select in an overflow hidden container
    var selectBox = $('.product_pod select'),
        isIE = navigator.userAgent.toLowerCase().indexOf("msie");
    if (isIE > -1) {
      selectBox.on({
        mousedown: function(){
          $(this).addClass("select-open");
        },
        change: function(){
          $(this).removeClass("select-open");
        }
      });
    }

});
