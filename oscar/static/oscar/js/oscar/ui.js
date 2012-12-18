var oscar = (function(o, $) {
    // Replicate Django's flash messages so they can be used by AJAX callbacks.
    o.messages = {
        icons: {
            'info': '<i class="icon-info-sign"></i>',
            'success': '<i class="icon-ok-sign"></i>',
            'warning': '<i class="icon-warning-sign"></i>',
            'error': '<i class="icon-exclamation-sign"></i>'
        },
        addMessage: function(tag, msg) {
            var iconHTML = o.messages.icons[tag],
                msgHTML = '<div class="alert fade in alert-' + tag + '">' +
                '<a href="#" class="close" data-dismiss="alert">x</a>' + iconHTML + " " + msg +
                '</div>';
            $('#messages').append($(msgHTML));
        },
        debug: function(msg) { o.messages.addMessage('debug', msg); },
        info: function(msg) { o.messages.addMessage('info', msg); },
        success: function(msg) { o.messages.addMessage('success', msg); },
        warning: function(msg) { o.messages.addMessage('warning', msg); },
        error: function(msg) { o.messages.addMessage('error:', msg); }
    };

    // Notifications inbox within 'my account' section.
    o.notifications = {
        init: function() {
            $('a[data-behaviours~="archive"]').click(function() {
                o.notifications.checkAndSubmit($(this), 'archive');
            });
            $('a[data-behaviours~="delete"]').click(function() {
                o.notifications.checkAndSubmit($(this), 'delete');
            });
        },
        checkAndSubmit: function($ele, btn_val) {
            $ele.closest('tr').find('input').attr('checked', 'checked');
            $ele.closest('form').find('button[value="' + btn_val + '"]').click();
            return false;
        }
    };

    // Site-wide forms events
    o.forms = {
        init: function() {
            // Forms with this behaviour are 'locked' once they are submitted to
            // prevent multiple submissions
            $('form[data-behaviours~="lock"]').submit(o.forms.submitIfNotLocked);

            // Disable buttons when they are clicked
            $('.js-disable-on-click').click(function(){$(this).button('loading');});
        },
        submitIfNotLocked: function(event) {
            $form = $(this);
            if ($form.data('locked')) {
                return false;
            }
            $form.data('locked', true);
        }
    };

    return o;

})(oscar || {}, jQuery);

$(function(){oscar.forms.init();});


// TODO - rewrite the below JS to git into the oscar object, splitting the functionality 
// into SRP methods.
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
        $browse_open = $browse.parent().find('> button[data-toggle]');
    
        if (window_width > 767) {
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

    if (window_width > 767) {
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
    
    //Account / Profile navigation
    var checkHash = document.location.hash,
        getId = checkHash.substring(1),
        activeClass = $('.account-profile .tabbable'),
        aHref = $('a[href=' + checkHash + ']').closest('li');
    if (checkHash) {
      activeClass.find('.active').removeClass('active');
      $('#' + getId).add(aHref).addClass('active');
    }

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
